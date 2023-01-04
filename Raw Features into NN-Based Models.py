# -*- coding: utf-8 -*-
"""Capstone Assignment 14 RNN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AdKD6S6IZ_zLxulQM7UGgXy9Xdn2XJlv
"""

'''
Task: Stock market prediction with classification -> Predict whether the prices will rise or fall in the next day.
Companies: Apple and Procter & Gamble
Model: RNN
Features: historical stock market closing prices
Time series: take into account time sequences
Dataset: yfinance module
Implementation:
  1) Prepare the dataframe
  2) Train the model
  3) Make predictions
'''

#Load the dataset
!pip install yfinance

#Import statements
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import math
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split 
from sklearn.metrics import f1_score
from sklearn.metrics import confusion_matrix as cmatrix
import numpy as np
import warnings
warnings.filterwarnings("ignore")
from sklearn.metrics import plot_confusion_matrix
import tensorflow as tf
from tensorflow import keras
from keras import layers
from keras.layers import Flatten
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.preprocessing import MinMaxScaler
from datetime import timedelta
import datetime
from sklearn.utils import resample
from tensorflow import keras
from keras.models import Sequential
from keras import layers
from keras.layers import LSTM, Dropout, Dense, Conv1D, MaxPooling1D
from collections import deque
import random
from keras.callbacks import TensorBoard, ModelCheckpoint
import time
from itertools import chain
from sklearn.metrics import accuracy_score
from sklearn.utils import shuffle 
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.metrics import confusion_matrix
import seaborn as sns

'''
This function takes in a dataframe that holds the prices and labels of multiple companies.
It returns the X and y values of each company.
The X values are put into sequences of 5 prices each to signify the 5 previous data points.
Then I shuffle the sequences because the sequences hold time information and company information within themselves.
'''
def get_sequences(df, companies, seq_len):
  #holds the first letter of the company name in the dataframe index
  first_company = df.index[0][0]
  #will hold a list of all the 5 previous day's prices of the first company
  temp_sequential_data_1 = []
  #will hold a list of all the 5 previous day's prices of the second company
  temp_sequential_data_2 = []
  #will hold a list of all the 5 previous day's prices of both of the companies
  sequential_data = []
  #will update the sequence of 5 previous days
  prev_days_1 = deque(maxlen=seq_len)
  prev_days_2 = deque(maxlen=seq_len)
  #holds all sequential X and y values of each company
  X1 = []
  X2 = []
  y = []
  #tells us if we moved on to the next company already
  switched = False 
  #keeps track of the index
  index = 0 

  for i in df[[('Close'), ('Company'), ('Rise')]].values:
    if(df.index[index][0] != first_company):
      prev_days_2.append(i[0])
      if len(prev_days_2) == seq_len:
        temp_sequential_data_2.append([np.array(prev_days_2), i[-2], i[-1]])
      switched = True
    else:
      prev_days_1.append(i[0])
      if len(prev_days_1) == seq_len:
        temp_sequential_data_1.append([np.array(prev_days_1), i[-2], i[-1]])
    index = index + 1

  sequential_data = temp_sequential_data_1 + temp_sequential_data_2

  #shuffle the sequential data. The sequences themselves already have time relationship information that the model
  #should be able to pick up on and the order the sequences are placed shouldn't matter.
  random.shuffle(sequential_data)

  for seq, comp, label in sequential_data:
    X1.append(seq)
    X2.append(comp)
    y.append(label)

  return np.array(X1), np.array(X2), np.array(y)
#########################################################################################################################
#Split the data into train, validation, and test sets
#64% train, 16% validation, 20% test
def split_data(data, companies):
  #Declare the data sets
  train_data = pd.DataFrame()
  valid_data = pd.DataFrame()
  test_data = pd.DataFrame()

  #Calculate the values of where to split the data
  tot_len = len(data)
  train_len = int(tot_len * 0.64) 
  valid_len = train_len + int(tot_len * 0.16)

  #Get the train, validation, and test data
  train_data = data.iloc[0:train_len]
  valid_data = data.iloc[train_len:valid_len]
  test_data = data.iloc[valid_len:]

  #Put the data in order chronologically and by company
  train_data = reorder_data(train_data)
  valid_data = reorder_data(valid_data)
  test_data = reorder_data(test_data)

  return train_data, valid_data, test_data
#########################################################################################################################
#Function to get one day in the future from the end date in order to calculate the labels
def get_adjusted_end_date(sd, interv, days_ahead):
  x = sd.split('-')
  year = int(x[0])
  month = int(x[1])
  day = int(x[2])
  x = datetime.datetime(year, month, day)
  if(interv == '1d'):
    date = x + timedelta(days=days_ahead)
  elif(interv == '1wk'):
    date = x + timedelta(weeks=days_ahead)
  else:
    date = x + timedelta(months=days_ahead)

  date = str(date)
  date = date.split(' ')
  date = date[0]

  return date
#########################################################################################################################
#Function to download one future day as well
def get_adjusted_dataframe(data, companies, sd, ed, interv):
  orig_len = len(data)
  days_ahead = 1
  new_ed = ed
  while(len(data) < orig_len + 1):
    data = pd.DataFrame()
    new_ed = get_adjusted_end_date(new_ed, interv, days_ahead)
    data = yf.download(tickers=companies, start=sd, end=new_ed, interval=interv)

  return data
#########################################################################################################################
#This function calculates the labels and the number of rise and fall data points
def get_labels(data, companies):
  #keep track of the number of rise and fall data points
  rise = 0
  fall = 0

  #create a list to hold the labels
  label = list()

  #This variable will distinguish the companies from each other
  j = 0
  
  for ticker in companies:
    data = data.drop(columns=[('Adj Close', ticker), ('High', ticker), ('Low', ticker), ('Open', ticker), ('Volume', ticker)])

    #Create the label column and the company column
    lab = list()
    coms = list()
    y = list(data[('Close', ticker)].pct_change())
    y.pop(0)
    for i in range(len(y)):
      num = str(y[i]) #get the percent change as a string in order to tell if it is negative or positive.
      coms.append(j) #save the company
      if num[0] == '-':
        lab.append(0) #save the label, 0 = Fall
        fall += 1 #sum of the number of fall data points
      elif num[0] != '-':
        lab.append(1) #save the label, 1 = Rise
        rise += 1 #sum of the number of rise data points
    lab.append(np.nan) #append nan to the end of labels because we are going to drop the last day from the dataframe
    coms.append(j) #append one more to the end of coms so that the length is the same as the lab length (we will drop last element of each company anyway)
    j += 1
    data[('Company'), ticker] = coms
    data[('Rise', ticker)] = lab

  #Delete the last row
  data = data.drop(data.index[-1])

  return data, rise, fall
#########################################################################################################################
#This function drops the excess fall or rise data points in the data set so that there are an equal number of both
def downsample_data(data, rise, fall, companies):
  #Downsample the majority class if the split is greater than 51%-49% so that there will be an equal 
  #(or close to equal) number of Fall and Rise data points
  df_new = pd.DataFrame()
  tot_samples = rise + fall
  if ((rise/tot_samples) > 0.51):
    if (rise < fall):
      df_min = data[data.Rise == 1]
      df_maj = data[data.Rise == 0]
    else:
      df_min = data[data.Rise == 0]
      df_maj = data[data.Rise == 1]

    df_maj_down = resample(df_maj, replace = False, n_samples = len(df_min), random_state = 0)
    df_new = pd.concat([df_min,df_maj_down])
  else:
    df_new = data

  return df_new
#########################################################################################################################
#This function combines both tickers so that the different pieces of information from each company can be in one 
#column in the dataframe, rather than each company have it's own columns
def combine_tickers(data, companies):
  close = list()
  company = list()
  rise = list()
  idx = list()

  for ticker in companies:
    #Get a list of the date and ticker so that we can rename the index of the dataframe
    for i in range(len(data.index)):
      new_str = str(data.index[i])
      new_new_str = new_str.split(' ')
      new_index =  new_new_str[0] + "_" + ticker 
      idx.append(new_index)
  
    #Save the information in lists that will be added to a new dataframe 
    for i in data[('Close', ticker)]:
      close.append(i)
    for i in data[('Company', ticker)]:
      company.append(i)
    for i in data[('Rise', ticker)]:
      rise.append(i)

  #Create a new dataframe
  df = pd.DataFrame()
  df['Close'] = close
  df['Company'] = company
  df['Rise'] = rise

  #rename the index numbers to be the date/company
  for i in range(len(df)):
    df.rename(index={i:idx[i]}, inplace=True)

  return df
#########################################################################################################################
#This function drops the excess fall or rise data points in the data set so that there are an equal number of both
def downsample_data(data, rise, fall, companies):
  #Downsample the majority class if the split is greater than 51%-49% so that there will be an equal 
  #(or close to equal) number of Fall and Rise data points
  df_new = pd.DataFrame()
  tot_samples = rise + fall
  if ((rise/tot_samples) > 0.51):
    if (rise < fall):
      df_min = data[data.Rise == 1]
      df_maj = data[data.Rise == 0]
    else:
      df_min = data[data.Rise == 0]
      df_maj = data[data.Rise == 1]

    df_maj_down = resample(df_maj, replace = False, n_samples = len(df_min), random_state = 0)
    df_new = pd.concat([df_min,df_maj_down])
  else:
    df_new = data

  df_new = df_new.sort_index()

  return df_new
#########################################################################################################################
def reorder_data(data):
  df = pd.DataFrame()
  df['Close'] = data['Close']
  df['Company'] = data['Company']
  df['Rise'] = data['Rise']
  index_list = list()

  #rename the index numbers to be the date/company
  for i in range(len(data)):
    s = str(data.index[i])
    new_s = s.split('_')
    new_indx =  new_s[1] + "_" + new_s[0] 
    index_list.append(new_indx)

  for i in range(len(df)):
    df.rename(index={df.index[i]:index_list[i]}, inplace=True)

  df = df.sort_index()
  
  return df
#########################################################################################################################
#Normalize the data - Avg Volume is the only one that needs to be normalized
def normalize_data(train, valid, test):
  #Create temporary dataframes for the train and valid datasets
  train_norm = pd.DataFrame()
  train_norm['Close'] = train['Close']

  valid_norm = pd.DataFrame()
  valid_norm['Close'] = valid['Close']

  test_norm = pd.DataFrame()
  test_norm['Close'] = test['Close']

  #define scaler
  scaler = StandardScaler()
  #fit only on the train dataset
  scaler = scaler.fit(train_norm) 

  #transform the train dataset
  train_norm = scaler.transform(train_norm)
  train_norm = list(train_norm)

  #transform the valid dataset with the scaler that is fitted with the train dataset
  valid_norm = scaler.transform(valid_norm)
  valid_norm = list(valid_norm)

  #transform the test dataset with the scaler that is fitted with the train dataset
  test_norm = scaler.transform(test_norm)
  test_norm = list(test_norm)

  #Remove the original data from the original dataframes, 
  #and put the normalized data into the original dataframes
  train = train.drop(columns=['Close'])
  valid = valid.drop(columns=['Close'])
  test = test.drop(columns=['Close'])
  train['Close'] = train_norm
  valid['Close'] = valid_norm
  test['Close'] = test_norm

  train['Close'] = train['Close'].str.get(0)
  valid['Close'] = valid['Close'].str.get(0)
  test['Close'] = test['Close'].str.get(0)
  
  return train, valid, test
#########################################################################################################################
#Fetch the historical stock market data from the yfinance module
def get_Features(companies, sd, ed, interv, seq_len):
  #Create an empty dataframe
  data = pd.DataFrame()
  #Download the historical data based on the parameters
  data = yf.download(tickers=companies, start=sd, end=ed, interval=interv)  
  #Get adjusted dataframe to add one day to the end of the dataframe
  data = get_adjusted_dataframe(data, companies, sd, ed, interv)
  #Drop the empty cells in the dataframe
  data = data.dropna()
  #Calculate the labels and add them to the dataframe
  data, rise, fall = get_labels(data, companies)
  #Make one column for Close and Rise rather than having seperate columns for each company
  #This makes it easier to downsample the data
  data = combine_tickers(data, companies)
  #Downsample the data
  data = downsample_data(data, rise, fall, companies)

  #64% train, 16% valid, 20% test
  train = pd.DataFrame() 
  valid = pd.DataFrame() 
  test = pd.DataFrame()
  train, valid, test = split_data(data, companies)

  # #normalize the data
  # train, valid, test = normalize_data(train, valid, test)

  X_train_seq, X_train_comp, y_train = get_sequences(train, companies, seq_len)
  X_valid_seq, X_valid_comp, y_valid = get_sequences(valid, companies, seq_len)
  X_test_seq, X_test_comp, y_test = get_sequences(test, companies, seq_len)

  return data, X_train_seq, X_train_comp, y_train, X_valid_seq, X_valid_comp, y_valid, X_test_seq, X_test_comp, y_test
#########################################################################################################################
#Function to assemble the final dataframe
def getData(companies, sd, ed, interv, seq_len):
  data = pd.DataFrame()
  X_train = pd.DataFrame()
  y_train = pd.DataFrame()
  X_valid = pd.DataFrame()
  y_valid = pd.DataFrame()
  X_test = pd.DataFrame()
  y_test = pd.DataFrame()

  data, X_train_seq, X_train_comp, y_train, X_valid_seq, X_valid_comp, y_valid, X_test_seq, X_test_comp, y_test = get_Features(companies, sd, ed, interv, seq_len)
  return data, X_train_seq, X_train_comp, y_train, X_valid_seq, X_valid_comp, y_valid, X_test_seq, X_test_comp, y_test

companies = ['AAPL', 'PG']
seq_len = 5 #5 days as the window
data, X_train_seq, X_train_comp, y_train, X_valid_seq, X_valid_comp, y_valid, X_test_seq, X_test_comp, y_test = getData(companies, '1999-12-31', '2020-01-02', "1d", seq_len)

print("LENGTH OF DATA SET:", len(data), "\n")
print("Data:\n", data)

print("--------------\n")

print("LENGTH OF TRAIN SET:", len(y_train), "\n")
print(X_train_seq)
print(X_train_comp)
print(y_train)

print("--------------\n")

print("LENGTH OF VALIDATION SET:", len(y_valid), "\n")
print(X_valid_seq)
print(X_valid_comp)
print(y_valid)

print("--------------\n")

print("LENGTH OF TEST SET:", len(y_test), "\n")
print(X_test_seq)
print(X_test_comp)
print(y_test)

#RNN
X_train_seq_rnn = X_train_seq 
X_train_comp_rnn = X_train_comp 
y_train_rnn = y_train

X_valid_seq_rnn = X_valid_seq 
X_valid_comp_rnn = X_valid_comp 
y_valid_rnn = y_valid

#RESHAPE THE INPUTS:
X_train_seq_rnn = np.reshape(X_train_seq_rnn, (X_train_seq_rnn.shape[0], X_train_seq_rnn.shape[1], 1)) #reshape input to be [# samples, # past time steps, # features]
X_train_comp_rnn = np.reshape(X_train_comp_rnn, (X_train_comp_rnn.shape[0], 1, 1)) #reshape input to be [# samples, # past time steps, # features]
y_train_rnn = np.reshape(y_train_rnn, (y_train_rnn.shape[0], 1, 1)) 

X_valid_seq_rnn = np.reshape(X_valid_seq_rnn, (X_valid_seq_rnn.shape[0], X_valid_seq_rnn.shape[1], 1)) #reshape input to be [# samples, # past time steps, # features]
X_valid_comp_rnn = np.reshape(X_valid_comp_rnn, (X_valid_comp_rnn.shape[0], 1, 1)) #reshape input to be [# samples, # past time steps, # features]
y_valid_rnn = np.reshape(y_valid_rnn, (y_valid_rnn.shape[0], 1, 1)) 

#TUNE THE HYPERPARAMETERS
  #batch size - number of randomly selected samples in each minibatch
B = [25, 35, 50] 
  #epochs - how many times to show the entire training set to the network
E = [25, 50, 100] 
  #neurons - number of neurons in LSTM layer and dense layer
N = [10, 20]
  #dropout - the ratio of the dropout layer
D = [0.2, 0.3]

checkpoints = []
cp_callbacks = []
for b in B:
  for e in E:
    for n in N:
      for d in D:
        #DECLARE CALLBACK
        checkpoints.append("model_" + datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
        cp_callbacks.append(ModelCheckpoint(
            filepath=checkpoints[-1],
            monitor='val_accuracy', 
            verbose=1, 
            save_best_only=True, 
            mode='max'))
        #ASSEMBLE THE MODEL:
          #shape=(lookback, n_features) -> (5, 1):
        close_input = keras.Input(shape=(X_train_seq_rnn.shape[1], X_train_seq_rnn.shape[2]), name="Close") 
          #shape=(lookback, n_features) -> (1, 1):
        company_input = keras.Input(shape=(X_train_comp_rnn.shape[1]), name ="Company") 
        lstm_input = LSTM(n, name="LSTM", activation='relu')(close_input)
        lstm_input2 = LSTM(n, name="LSTM_2", activation='relu')(close_input)
        concatenated_sequential = layers.concatenate([lstm_input, lstm_input2])
        concatenated = layers.concatenate([concatenated_sequential, company_input])
        dense_input = Dense(n, name="DENSE", activation='relu')(concatenated)
        dropout_input = Dropout(d)(dense_input)
        dense_input2 = Dense(n, name="DENSE_2", activation='relu')(dropout_input)
        dense_input3 = Dense(5, name="DENSE_3", activation='relu') (dense_input2)
        out = Dense(1, name="Rise", activation='sigmoid')(dense_input3) 
        model = keras.Model(inputs=[close_input, company_input], outputs=out)
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        
        #FIT THE MODEL WITH TRAINING DATA AND VALIDATION DATA
        model.fit({"Close":X_train_seq_rnn, "Company":X_train_comp_rnn}, {"Rise":y_train_rnn}, epochs=e, batch_size=b, verbose=2, 
                  callbacks=[cp_callbacks[-1]], validation_data=({"Close":X_valid_seq_rnn, "Company":X_valid_comp_rnn}, {"Rise":y_valid_rnn}))

print("All Saved Callbacks:", checkpoints)

max_val_acc = cp_callbacks[0].best
best_callback = cp_callbacks[0] #initialize best_callback to the first one
for i in range(len(cp_callbacks)):
  if cp_callbacks[i].best > max_val_acc:
    max_val_acc = cp_callbacks[i].best #update the max_val_acc
    best_callback = cp_callbacks[i] #update the best_callback if it currently has the max_val_acc

best_callback_checkpoint_path = best_callback._write_filepath
print("Best Callback Name:", best_callback._write_filepath)
print("Best Callback Accuracy:", best_callback.best)

from google.colab import drive 
drive.mount('/content/gdrive', force_remount=True)

model.save(F'/content/gdrive/My Drive/Saved Models/{best_callback_checkpoint_path}.h5'.format())

#Load the saved model
#Now, you don't need to train again or save all the models again!!
model = keras.models.load_model('/content/gdrive/MyDrive/Saved Models/model_10-28-2022-21-18-22.h5')

X_test_seq_rnn = X_test_seq 
X_test_comp_rnn = X_test_comp 
y_test_rnn = y_test
X_test_seq_rnn = np.reshape(X_test_seq_rnn, (X_test_seq_rnn.shape[0], X_test_seq_rnn.shape[1], 1)) #reshape input to be [# samples, # past time steps, # features]
X_test_comp_rnn = np.reshape(X_test_comp_rnn, (X_test_comp_rnn.shape[0], 1, 1)) #reshape input to be [# samples, # past time steps, # features]
# y_test_rnn = np.reshape(y_test_rnn, (y_test_rnn.shape[0], 1, 1))

#Predict
predictions = model.predict({"Close":X_test_seq_rnn, "Company":X_test_comp_rnn}, verbose = 0).flatten()
preds = []
for p in predictions:
  if p > 0.50:
    preds.append(1)
  else:
    preds.append(0)
print("\nClassification Report:\n", classification_report(y_true=y_test_rnn, y_pred=preds, digits=4))
print("\t    RNN Confusion Matrix:")
cf_matrix = confusion_matrix(y_test_rnn, preds)
group_names = ['True Neg', 'False Pos', 'False Neg', 'True Pos']
group_counts = ['{0:0.0f}'.format(value) for value in cf_matrix.flatten()]
labels = [f'{v1}\n{v2}' for v1, v2 in zip(group_names, group_counts)]
labels = np.asarray(labels).reshape(2,2)
sns.heatmap(cf_matrix, annot=labels, fmt='', cmap='PiYG')

#CNN
X_train_seq_cnn = X_train_seq 
X_train_comp_cnn = X_train_comp 
y_train_cnn = y_train

X_valid_seq_cnn = X_valid_seq 
X_valid_comp_cnn = X_valid_comp 
y_valid_cnn = y_valid

#RESHAPE THE INPUTS:
X_train_seq_cnn = np.reshape(X_train_seq_cnn, (X_train_seq_cnn.shape[0], X_train_seq_cnn.shape[1], 1)) #reshape input to be [# samples, # past time steps, # features]
X_train_comp_cnn = np.reshape(X_train_comp_cnn, (X_train_comp_cnn.shape[0], 1, 1)) #reshape input to be [# samples, # past time steps, # features]
y_train_cnn = np.reshape(y_train_cnn, (y_train_cnn.shape[0], 1, 1)) 

X_valid_seq_cnn = np.reshape(X_valid_seq_cnn, (X_valid_seq_cnn.shape[0], X_valid_seq_cnn.shape[1], 1)) #reshape input to be [# samples, # past time steps, # features]
X_valid_comp_cnn = np.reshape(X_valid_comp_cnn, (X_valid_comp_cnn.shape[0], 1, 1)) #reshape input to be [# samples, # past time steps, # features]
y_valid_cnn = np.reshape(y_valid_cnn, (y_valid_cnn.shape[0], 1, 1))  

#specify the filter
n_filters = (8, 8, 8)

#TUNE THE HYPERPARAMETERS
  #batch size - number of randomly selected samples in each minibatch
B = [25, 35, 50] 
  #epochs - how many times to show the entire training set to the network
E = [25, 50, 100] 
  #neurons - number of neurons in DENSE layers
N = [10, 20]
  #dropout - the ratio of the dropout layer
D = [0.2, 0.3]

cnn_checkpoints = []
cnn_cp_callbacks = []
for b in B:
  for e in E:
    for n in N:
      for d in D:
        #DECLARE CALLBACK
        cnn_checkpoints.append("model_" + datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
        cnn_cp_callbacks.append(ModelCheckpoint(
            filepath=cnn_checkpoints[-1],
            monitor='val_accuracy', 
            verbose=1, 
            save_best_only=True, 
            mode='max'))
        #ASSEMBLE THE MODEL:      
        close_input = keras.Input(shape=(X_train_seq_cnn.shape[1], X_train_seq_cnn.shape[2]), name="Close") 
        company_input = keras.Input(shape=(X_train_comp_cnn.shape[1]), name ="Company") 
        cnn = Conv1D(n_filters[0], kernel_size=2, name="CONV", activation='relu', input_shape=(seq_len, 1))(close_input)
        # cnn_2 = Conv1D(n_filters[1], kernel_size=2, name="CONV_2", activation='relu', input_shape=(seq_len, 1))(close_input)
        # concat = layers.concatenate([cnn, cnn_2])
        pool = MaxPooling1D(pool_size=2)(cnn)
        cnn_3 = Conv1D(n_filters[2], kernel_size=1, name="CONV_3", activation='relu')(pool)
        pool_2 = MaxPooling1D(pool_size=2)(cnn_3)
        flat = Flatten()(pool_2)
        drop = Dropout(d)(flat)
        concat_2 = layers.concatenate([drop, company_input])
        dense = Dense(n, name="DENSE", activation='relu')(concat_2)
        drop_2 = Dropout(d)(dense)
        dense_2 = Dense(n, name="DENSE_2", activation='relu')(drop_2)
        dense_3 = Dense(5, name="DENSE_3", activation='relu') (dense_2)
        out = Dense(1, name="Rise", activation='sigmoid')(dense_3) 
        model = keras.Model(inputs=[close_input, company_input], outputs=out)
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        
        #FIT THE MODEL WITH TRAINING AND VALIDATION DATA
        model.fit({"Close":X_train_seq_cnn, "Company":X_train_comp_cnn}, {"Rise":y_train_cnn}, epochs=e, batch_size=b, verbose=2, 
                  callbacks=[cnn_cp_callbacks[-1]], validation_data=({"Close":X_valid_seq_cnn, "Company":X_valid_comp_cnn}, {"Rise":y_valid_cnn}))

print("All Saved Callbacks:", cnn_checkpoints)

max_val_acc = cnn_cp_callbacks[0].best
cnn_best_callback = cnn_cp_callbacks[0] #initialize best_callback to the first one
for i in range(len(cnn_cp_callbacks)):
  if cnn_cp_callbacks[i].best > max_val_acc:
    max_val_acc = cnn_cp_callbacks[i].best #update the max_val_acc
    cnn_best_callback = cnn_cp_callbacks[i] #update the best_callback if it currently has the max_val_acc

cnn_best_callback_checkpoint_path = cnn_best_callback._write_filepath
print("Best Callback Name:", cnn_best_callback._write_filepath)
print("Best Callback Accuracy:", cnn_best_callback.best)

model.save(F'/content/gdrive/My Drive/Saved Models/{cnn_best_callback_checkpoint_path}.h5'.format())

#Load the saved model
#Now, you don't need to train again or save all the models again!!
model = keras.models.load_model('/content/gdrive/MyDrive/Saved Models/model_10-29-2022-21-33-38.h5')

X_test_seq_cnn = X_test_seq  
X_test_comp_cnn = X_test_comp 
y_test_cnn = y_test
X_test_seq_cnn = np.reshape(X_test_seq_cnn, (X_test_seq_cnn.shape[0], X_test_seq_cnn.shape[1], 1)) #reshape input to be [# samples, # past time steps, # features]
X_test_comp_cnn = np.reshape(X_test_comp_cnn, (X_test_comp_cnn.shape[0], 1, 1)) #reshape input to be [# samples, # past time steps, # features]
# y_test_cnn = np.reshape(y_test_cnn, (y_test_cnn.shape[0], 1, 1))

#Predict
predictions_2 = model.predict({"Close":X_test_seq_cnn, "Company":X_test_comp_cnn}, verbose = 0).flatten()
preds_2 = []
for p in predictions_2:
  if p > 0.50:
    preds_2.append(1)
  else:
    preds_2.append(0)
print("\nClassification Report:\n", classification_report(y_true=y_test_cnn, y_pred=preds_2, digits=4))
print("\t    CNN Confusion Matrix:")
cf_matrix = confusion_matrix(y_test_cnn, preds_2)
group_names = ['True Neg', 'False Pos', 'False Neg', 'True Pos']
group_counts = ['{0:0.0f}'.format(value) for value in cf_matrix.flatten()]
labels = [f'{v1}\n{v2}' for v1, v2 in zip(group_names, group_counts)]
labels = np.asarray(labels).reshape(2,2)
sns.heatmap(cf_matrix, annot=labels, fmt='', cmap='PiYG')

#FFNN
#Append the company information to the end of the window sequences of the closing prices
X_train_seq_ffnn = X_train_seq
X_train_comp_ffnn = X_train_comp 
y_train_ffnn = y_train

X_valid_seq_ffnn = X_valid_seq 
X_valid_comp_ffnn = X_valid_comp 
y_valid_ffnn = y_valid

#RESHAPE THE INPUTS
X_train_comp_ffnn = X_train_comp_ffnn.reshape(-1, 1)
X_valid_comp_ffnn = X_valid_comp_ffnn.reshape(-1, 1)

#TUNE THE HYPERPARAMETERS
  #batch size - number of randomly selected samples in each minibatch
B = [25, 35, 50] 
  #epochs - how many times to show the entire training set to the network
E = [25, 50, 100] 
  #neurons - number of neurons in DENSE layers
N = [5, 10, 30]

ffnn_checkpoints = []
ffnn_cp_callbacks = []
#Train the model with different hyperparameters
for b in B:
  for e in E:
    for n in N:
      #DECLARE CALLBACK
      ffnn_checkpoints.append("model_" + datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
      ffnn_cp_callbacks.append(ModelCheckpoint(
          filepath=ffnn_checkpoints[-1],
          monitor='val_accuracy', 
          verbose=1, 
          save_best_only=True, 
          mode='max'))
      #ASSEMBLE THE MODEL
      close_input = keras.Input(shape=(X_train_seq_ffnn.shape[1],), name="close") #shape is window size
      comp_input = keras.Input(shape=(X_train_comp_ffnn.shape[1],), name="company") 

      concat = layers.concatenate([close_input, comp_input])

      dense_1 = Dense(n, activation='relu', input_dim=seq_len+1)(concat)
      dense_2 = Dense(n, activation='relu')(dense_1)   
      out = Dense(1, name="Rise", activation='sigmoid')(dense_2)    
      model = keras.Model(inputs=[close_input, comp_input], outputs=out)
      model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
          
      #FIT THE MODEL WITH TRAINING DATA AND VALIDATION DATA
      model.fit({"close":X_train_seq_ffnn, "company":X_train_comp_ffnn}, {"Rise":y_train_ffnn}, epochs=e, batch_size=b, verbose=2, 
            callbacks=[ffnn_cp_callbacks[-1]], validation_data=({"close":X_valid_seq_ffnn, "company":X_valid_comp_ffnn}, {"Rise":y_valid_ffnn}))

print("All Saved Callbacks:", ffnn_checkpoints)

max_val_acc = ffnn_cp_callbacks[0].best
ffnn_best_callback = ffnn_cp_callbacks[0] #initialize best_callback to the first one
for i in range(len(ffnn_cp_callbacks)):
  if ffnn_cp_callbacks[i].best > max_val_acc:
    max_val_acc = ffnn_cp_callbacks[i].best #update the max_val_acc
    ffnn_best_callback = ffnn_cp_callbacks[i] #update the best_callback if it currently has the max_val_acc

ffnn_best_callback_checkpoint_path = ffnn_best_callback._write_filepath
print("Best Callback Name:", ffnn_best_callback._write_filepath)
print("Best Callback Accuracy:", ffnn_best_callback.best)

model.save(F'/content/gdrive/My Drive/Saved Models/{ffnn_best_callback_checkpoint_path}.h5'.format())

#Load the saved model
#Now, you don't need to train again or save all the models again!!
model = keras.models.load_model('/content/gdrive/MyDrive/Saved Models/model_11-11-2022-20-08-58.h5')

X_test_seq_ffnn = X_test_seq 
X_test_comp_ffnn = X_test_comp 
y_test_ffnn = y_test
X_test_comp_ffnn = X_test_comp_ffnn.reshape(-1, 1)

#Predict
predictions_3 = model.predict({"close":X_test_seq_ffnn, "company":X_test_comp_ffnn}, verbose = 0).flatten()
preds_3 = []
for p in predictions_3:
  if p > 0.50:
    preds_3.append(1)
  else:
    preds_3.append(0)
print("\nClassification Report:\n", classification_report(y_true=y_test_ffnn, y_pred=preds_3, digits=4))
print("\t    FFNN Confusion Matrix:")
cf_matrix = confusion_matrix(y_test_ffnn, preds_3)
group_names = ['True Neg', 'False Pos', 'False Neg', 'True Pos']
group_counts = ['{0:0.0f}'.format(value) for value in cf_matrix.flatten()]
labels = [f'{v1}\n{v2}' for v1, v2 in zip(group_names, group_counts)]
labels = np.asarray(labels).reshape(2,2)
sns.heatmap(cf_matrix, annot=labels, fmt='', cmap='PiYG')
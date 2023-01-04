# Senior-Project
Stock market prediction with classification

For my senior capstone project at CSU Channel Islands I did stock market prediction. 
Here is a link to my website that contains my poster and a video presentation: http://demalgeri.cikeys.com/28-2/

The following paragraphs are a summary of my project:

In my research, I used ML classification techniques to predict whether the stock 
price would rise or fall on the next day for the two companies, Apple and Procter & 
Gamble. To do so, I employed various classifiers trained by different sets of features. 

I fed historical stock market data to the models and 
trained the models so that they could predict whether the price would rise or fall in 
the next day. In this research, I have used two types of models: classical ML models and 
neural network (NN) based models. The classical ML models were trained by 
handcrafted features calculated from the historical stock data and NN based models 
were trained by raw features from the historical stock data.

The question I pursued was about which of these scenarios produced a better 
prediction accuracy:
• Classical ML models trained with handcrafted features
• NN based models trained with raw features
• Classical ML models trained with both raw and handcrafted features
• NN based models trained with both raw and handcrafted features

My initial hypothesis was that the NN based models with raw features or a
combination of raw and handcrafted features would have better prediction accuracy
than the classical ML models.

The result is interesting because the NN based models are designed to handle sequential data.
One explanation could be that the task is very complicated and tuning the architecture
for NN is difficult. In addition, the used data might not be sufficient for training RNNs.
Another reason could be that the used features were perhaps not indicative enough of
the stock market trend for the models to make more accurate predictions. The
features I chose from my research were based off research done by the IEEE. A
future path of this research could be choosing more or different features for training
the models.

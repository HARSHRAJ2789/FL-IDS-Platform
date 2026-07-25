import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
import logging

class LocalTrainer:
    def __init__(self, input_dim=196):
        self.input_dim = input_dim
        self.model = self.build_model()
        
    def build_model(self):
        model = models.Sequential([
            layers.Dense(256, activation='relu', input_shape=(self.input_dim,)),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        return model

    def set_weights(self, weights_list_of_arrays):
        if weights_list_of_arrays:
            self.model.set_weights(weights_list_of_arrays)

    def get_weights(self):
        return self.model.get_weights()

    def train(self, X, y, epochs, batch_size):
        if len(X) == 0:
            logging.info("No data to train on.")
            return {}
            
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            verbose=0,
            validation_split=0.1
        )
        return history.history

    def predict(self, X):
        if len(X) == 0:
            return np.array([])
        return self.model.predict(X, verbose=0)

    def save_model(self, path):
        path_str = str(path)
        if not path_str.endswith('.h5') and not path_str.endswith('.keras'):
            path_str += '.h5'
        self.model.save(path_str)

    def load_model(self, path):
        path_str = str(path)
        if not os.path.exists(path_str):
            if os.path.exists(path_str + '.h5'):
                path_str += '.h5'
            elif os.path.exists(path_str + '.keras'):
                path_str += '.keras'
        
        if os.path.exists(path_str):
            self.model = keras.models.load_model(path_str)
            return True
        return False

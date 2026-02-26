import os
import joblib
import pandas as pd
from django.conf import settings

class PredictionService:
    @staticmethod
    def predict_delivery_risk(order_to_sched, weight_kg, quantity, origin_enc, dest_enc, vendor_enc):
        """
        Loads the trained sklearn model and returns a prediction result.
        """
        model_path = os.path.join(settings.BASE_DIR, 'delay_model.pkl')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError("Trained model not found. Please ensure the model is trained and saved as .pkl file.")
            
        try:
            model = joblib.load(model_path)
            
            # Prepare feature dictionary. We assume the model expects these features.
            features = {
                'order_to_sched': order_to_sched,
                'weight_kg': weight_kg,
                'quantity': quantity,
                'origin_enc': origin_enc,
                'dest_enc': dest_enc,
                'vendor_enc': vendor_enc
            }
            
            # Predict using a DataFrame
            features_df = pd.DataFrame([features])
            
            result = model.predict(features_df)[0]
            
            # Map the result to "On Time" or "Late Risk"
            # It handles numeric 1/0 or strings if the model returns them directly.
            if result == 1 or str(result).lower() in ['1', 'true', 'late risk', 'late', 'delayed']:
                return "Late Risk"
            else:
                return "On Time"
                
        except Exception as e:
            raise Exception(f"Model prediction failed: {str(e)}")

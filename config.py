import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = "models/gemini-2.5-flash"
    
    MIN_TEST_CASES = 20
    POSITIVE_RATIO = 0.5  
    
    OUTPUT_JSON = "generated_tests.json"
    OUTPUT_CSV = "test_cases.csv"
    
    @staticmethod
    def validate():
        """Validate configuration"""
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        print(" Configuration loaded successfully")
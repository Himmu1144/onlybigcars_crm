import json
import django
import os
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_backend.settings')
django.setup()

from core.models import CarBrand, CarModel

def load_car_data(json_file_path):
    try:
        # Read JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        # Counter for tracking progress
        brands_created = 0
        models_created = 0
        brands_skipped = 0
        models_skipped = 0

        # Process brands and their models
        for brand_name in data['brands']:
            # Create brand if it doesn't exist
            brand, brand_created = CarBrand.objects.get_or_create(name=brand_name)
            
            if brand_created:
                brands_created += 1
            else:
                brands_skipped += 1

            # Get models for this brand
            if brand_name in data['models']:
                for model_name in data['models'][brand_name]:
                    # Create model if it doesn't exist
                    model, model_created = CarModel.objects.get_or_create(
                        brand=brand,
                        name=model_name
                    )
                    
                    if model_created:
                        models_created += 1
                    else:
                        models_skipped += 1

        # Print summary
        print(f"\nData import completed successfully!")
        print(f"Brands: {brands_created} created, {brands_skipped} already existed")
        print(f"Models: {models_created} created, {models_skipped} already existed")

    except FileNotFoundError:
        print(f"Error: Could not find the file at {json_file_path}")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in the file")
    except django.db.utils.IntegrityError as e:
        print(f"Database integrity error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Check if file path is provided as command line argument
    if len(sys.argv) > 1:
        json_file_path = sys.argv[1]
    else:
        json_file_path = 'cars.json'  # default path
    
    load_car_data(json_file_path)
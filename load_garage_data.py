import json
import django
import os


# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_backend.settings')
django.setup()

from core.models import Garage

def load_garage_data(garages_data):
    try:
        garages_created = 0
        garages_skipped = 0
        
        for garage in garages_data:
            # Clean the mobile number (remove spaces and potential formatting)
            mobile = garage['mobile'].replace(' ', '').split('/')[0]  # Take first number if multiple
            
            # Clean the link (remove leading/trailing spaces)
            link = garage['link'].strip() if garage['link'] != 'NA' else None
            
            # Try to create or update the garage
            garage_obj, created = Garage.objects.update_or_create(
                name=garage['name'],
                defaults={
                    'mechanic': garage['mechanic'],
                    'locality': garage['locality'],
                    'link': link,
                    'mobile': mobile,
                    'is_active': True
                }
            )
            
            if created:
                garages_created += 1
            else:
                garages_skipped += 1
                
        print(f"\nData import completed successfully!")
        print(f"Garages: {garages_created} created, {garages_skipped} updated")
            
    except django.db.utils.IntegrityError as e:
        print(f"Database integrity error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# The garage data as a Python list
garages = [
    {
        "name": "Onlybigcars - Automan Car",
        "mechanic": "Abhijit Sir",
        "locality": "16-347, NH75, Sharadamba Nagar, Muthyala Nagar, Bahubali Nagar, Jalahalli, Bengaluru, Karnataka 560013",
        "link": "https://maps.app.goo.gl/7mGMQPHUQKyqP8vx6",
        "mobile": "9663663100"
    },
    {
        "name": "Onlybigcars - Throttle Car 2",
        "mechanic": "NA",
        "locality": "Manjunatha layout, thubarahalli, munnekollal, Bangalore 560066",
        "link": "https://maps.app.goo.gl/JpiJajyrJ2zQRLE19",
        "mobile": "9964513326"
    },
    {
        "name": "Onlybigcars - Torquee Motors",
        "mechanic": "NA",
        "locality": "Chaithiyana Annanya, opp to lakshmi Hyundai, seegehalli, Bangalore 560067",
        "link": "https://maps.app.goo.gl/SmYfKxQeoVyvD5Dm6",
        "mobile": "9964513326"
    },
    {
        "name": "Onlybigcars - Throttle Car 1",
        "mechanic": "NA",
        "locality": "Avalahalli main road, virgonagar post, Rampura, Bangalore 560049",
        "link": "https://maps.app.goo.gl/8mURXvzU96Gts1Bz5",
        "mobile": "9964513326"
    },
    {
        "name": "Onlybigcars - Super Cars",
        "mechanic": "NA",
        "locality": "51, Dinnur main road, post, RT Nagar, Bengaluru, Karnataka 560032",
        "link": "https://maps.app.goo.gl/3YBwxLdkdLk4ei4a8",
        "mobile": "9341701325"
    },
    {
        "name": "Onlybigcars - Super Motors, vikaspuri",
        "mechanic": "NA",
        "locality": "Rd Number 237, LIG MIG flats, Pocket A, Hastsal, Delhi, 110066",
        "link": "https://maps.app.goo.gl/aRRuVn7sQ2XNi2HW6",
        "mobile": "8447770864"
    },
    {
        "name": "Onlybigcars - Motor Masters, Wazirpur",
        "mechanic": "NA",
        "locality": " Block B, Wazirpur Industrial Area, Ashok Vihar, Delhi, 110052",
        "link": "https://maps.app.goo.gl/jMxKDGsyeKcQym7o9",
        "mobile": "9999902802"
    },
    {
        "name": "Onlybigcars - Motor Masters, jahangirpuri ",
        "mechanic": "Keshav Gupta",
        "locality": "1st Floor, No 69, Udyog Nagar, New Delhi, Delhi 110033 ",
        "link": " https://maps.app.goo.gl/qHgtiEPGYXWubeXJ6",
        "mobile": "9999902802"
    },
    {
        "name": "Onlybigcars - Rathi Motors ",
        "mechanic": "Ajay(shree shyam motor)",
        "locality": "S No 2, Max Road, Shalamar, Shalimar Village, Shalimar Bagh, New Delhi, Delhi, 110088 ",
        "link": "https://maps.app.goo.gl/ZTkmQQ8jbdHNFuK88",
        "mobile": "9891123345"
    },
    {
        "name": "Onlybigcars - Shree Shyaam ji Automobile",
        "mechanic": "Ajay",
        "locality": "C109, Prahlad Vihar, Prahladpur, Rohini, New Delhi, Delhi, 110042",
        "link": "https://maps.app.goo.gl/QBejcra9xVa33Srg8",
        "mobile": "9891123345"
    },
    {
        "name": "Onlybigcars - Shiv Motors banker narela",
        "mechanic": "kala mistri/Neeraj7",
        "locality": "61, Ground Trunk Rd, Banker, narela ",
        "link": "https://maps.app.goo.gl/46MYYsFxbT8UkFUGA",
        "mobile": "8750322544/7206335057"
    },
    {
        "name": "Onlybigcars - Poorvi Auto Works ",
        "mechanic": "Ankur",
        "locality": "H8RJ+9PF, Noida, Uttar Pradesh",
        "link": "-https://maps.app.goo.gl/8w3kbRu8uMGeDPxL7",
        "mobile": "8588005112"
    },
    {
        "name": "Onlybigcars - Thrust Automobile",
        "mechanic": "Jayanth ",
        "locality": " 36/4 , K Narayanpura cross, Bagalur main road, Hennur Gardens, Bengaluru, Karnataka 560077",
        "link": " https://maps.app.goo.gl/65mrdNpwpAgQCiDX8?g_st=iw",
        "mobile": "7406644647"
    },
    {
        "name": "Onlybigcars - Grace Automobiles",
        "mechanic": "Sonu Sagar",
        "locality": "G62G+5WX New Delhi, Delhi",
        "link": "https://maps.app.goo.gl/4La3ZzEv2h9tzVqMA",
        "mobile": "99103 18266"
    },
    {
        "name": "Onlybigcars - X Plus auto",
        "mechanic": "Syed Nadeem",
        "locality": "388, 7th Block, 1st \"A\" Cross, Koromangala layout, Bangalore - 560095",
        "link": "https://maps.app.goo.gl/ttxRNAFUKAYpKWQy7",
        "mobile": "9060786198"
    },
    {
        "name": "Onlybigcars -Sadhna Motors Jahangirpuri ",
        "mechanic": "Rajnish Rajputh",
        "locality": "SSI 45 Rajasthan udyog nagar Jahangirpuri Services - Service & Repairing, AC Service & Repaire, Denting & Painting, Battery, Tyres, Detailing Services, Windshields & Light",
        "link": "https://maps.app.goo.gl/sFVZfU2Z6umqC4FA7 ",
        "mobile":  "9999152251"
    },
    {
        "name": "Onlybigcars - Company Workshop farmhouse",
        "mechanic": "NA",
        "locality": "99Q8+757, Faridabad, Haryana",
        "link": "https://maps.app.goo.gl/K93VYqtpJWD6vmmz9",
        "mobile": "99999-67591"
    },
    {
        "name": "Onlybigcars - Agra Mathura Road",
        "mechanic": "NA",
        "locality": "98V7+C38, Faridabad, Haryana",
        "link": "https://maps.app.goo.gl/XUswRwjuf1Xdv1W19",
        "mobile": "9999967591"
    },
    {
        "name": "Onlybigcars - 3A Car Service",
        "mechanic": "NA",
        "locality": "3A car service, Begur Rd, near St Francis School, Maruthi Layout, Hongasandra, Bengaluru, Karnataka 560068, India",
        "link": "https://maps.app.goo.gl/4AsP9DiRgkF3yX3w9",
        "mobile": "8123497166"
    },
    {
        "name": "Onlybigcars - Raghav Automobile",
        "mechanic": "Santosh Raghav",
        "locality": "Service & Repairing, AC Service & Repaire, Denting & Painting, Detailing Services, Windshields & Light",
        "link": "NA",
        "mobile": "7827130743"
    },
    {
        "name": "Onlybigcars - Indo German workshop",
        "mechanic": "Name - Sanjay",
        "locality": "Service & Repairing, AC Service & Repaire, Denting & Painting, Detailing Services, Windshields & Light",
        "link": "NA",
        "mobile": "9811116043"
    },
    {
        "name": "Onlybigcars - Luxury car care",
        "mechanic": "Dipak ji",
        "locality": "Service & Repairing, AC Service & Repaire, Denting & Painting, Battery, Tyres, Detailing Services, Windshields & Light",
        "link": "NA",
        "mobile": "9354627795"
    },
    {
        "name": "Onlybigcars - Own",
        "mechanic": "Sahil",
        "locality": "Service & Repairing, AC Service & Repaire, Denting & Painting, Windshields & Light, Battery & Tyres",
        "link": "https://g.co/kgs/X7g95w8",
        "mobile": "8368092684"
    },
    
    # ... rest of your garage data
]

if __name__ == "__main__":
    load_garage_data(garages)
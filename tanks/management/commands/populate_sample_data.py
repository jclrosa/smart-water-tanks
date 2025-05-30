from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
import random
from tanks.models import WaterTank, Sensor, SensorData, Alert


class Command(BaseCommand):
    help = 'Populate database with sample water tank data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample water tank data...')
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        # Sample tank data
        tank_data = [
            {
                'name': 'Manhattan Tower A',
                'location': '123 Broadway, New York, NY 10001',
                'borough': 'manhattan',
                'tank_type': 'rooftop',
                'capacity_gallons': 50000,
                'building_name': 'Broadway Tower',
                'building_owner': 'NYC Properties LLC',
                'contact_email': 'manager@nycproperties.com',
                'contact_phone': '+1 (212) 555-0101',
                'latitude': 40.7589,
                'longitude': -73.9851,
            },
            {
                'name': 'Brooklyn Heights Tank 1',
                'location': '456 Hicks Street, Brooklyn, NY 11201',
                'borough': 'brooklyn',
                'tank_type': 'rooftop',
                'capacity_gallons': 35000,
                'building_name': 'Heights Residential',
                'building_owner': 'Brooklyn Housing Corp',
                'contact_email': 'maintenance@brooklynhousing.com',
                'contact_phone': '+1 (718) 555-0102',
                'latitude': 40.6962,
                'longitude': -73.9936,
            },
            {
                'name': 'Queens Industrial Tank',
                'location': '789 Northern Blvd, Queens, NY 11372',
                'borough': 'queens',
                'tank_type': 'ground',
                'capacity_gallons': 100000,
                'building_name': 'Industrial Complex B',
                'building_owner': 'Queens Industrial Partners',
                'contact_email': 'ops@queensindustrial.com',
                'contact_phone': '+1 (718) 555-0103',
                'latitude': 40.7505,
                'longitude': -73.8776,
            },
            {
                'name': 'Bronx Hospital Tank',
                'location': '321 Grand Concourse, Bronx, NY 10451',
                'borough': 'bronx',
                'tank_type': 'elevated',
                'capacity_gallons': 75000,
                'building_name': 'Bronx Medical Center',
                'building_owner': 'NYC Health System',
                'contact_email': 'facilities@bronxmedical.org',
                'contact_phone': '+1 (718) 555-0104',
                'latitude': 40.8176,
                'longitude': -73.9276,
            },
            {
                'name': 'Staten Island Residential',
                'location': '654 Victory Blvd, Staten Island, NY 10301',
                'borough': 'staten_island',
                'tank_type': 'basement',
                'capacity_gallons': 25000,
                'building_name': 'Victory Apartments',
                'building_owner': 'SI Residential Management',
                'contact_email': 'super@victoryapts.com',
                'contact_phone': '+1 (718) 555-0105',
                'latitude': 40.6501,
                'longitude': -74.1134,
            },
        ]
        
        # Create tanks
        tanks = []
        for tank_info in tank_data:
            tank, created = WaterTank.objects.get_or_create(
                name=tank_info['name'],
                defaults={
                    **tank_info,
                    'installation_date': date(2020, 1, 1),
                    'status': random.choice(['active', 'active', 'active', 'maintenance']),
                    'created_by': admin_user,
                }
            )
            tanks.append(tank)
            if created:
                self.stdout.write(f'Created tank: {tank.name}')
        
        # Create sensors for each tank
        sensor_types = ['level', 'temperature', 'ph', 'turbidity']
        for tank in tanks:
            for sensor_type in sensor_types:
                sensor, created = Sensor.objects.get_or_create(
                    tank=tank,
                    sensor_type=sensor_type,
                    defaults={
                        'model_number': f'SEN-{sensor_type.upper()}-2024',
                        'serial_number': f'{tank.name[:3].upper()}-{sensor_type.upper()}-{random.randint(1000, 9999)}',
                        'installation_date': date(2020, 1, 15),
                        'status': random.choice(['active', 'active', 'active', 'low_battery']),
                        'battery_level': random.randint(20, 100),
                        'calibration_offset': random.uniform(-0.5, 0.5),
                    }
                )
                if created:
                    self.stdout.write(f'Created sensor: {sensor}')
        
        # Generate sensor data for the last 30 days
        self.stdout.write('Generating sensor data...')
        start_date = timezone.now() - timedelta(days=30)
        
        for tank in tanks:
            # Generate data points every hour for the last 30 days
            current_time = start_date
            base_level = random.uniform(30, 80)  # Base water level percentage
            base_temp = random.uniform(45, 65)   # Base temperature in Fahrenheit
            base_ph = random.uniform(6.5, 8.5)   # Base pH level
            
            while current_time <= timezone.now():
                # Add some realistic variation
                level_variation = random.uniform(-5, 5)
                temp_variation = random.uniform(-3, 3)
                ph_variation = random.uniform(-0.3, 0.3)
                
                water_level = max(0, min(100, base_level + level_variation))
                water_temp = base_temp + temp_variation
                ph_level = max(0, min(14, base_ph + ph_variation))
                
                # Simulate some tank usage patterns (lower levels during day)
                hour = current_time.hour
                if 6 <= hour <= 22:  # Daytime usage
                    water_level *= random.uniform(0.85, 0.95)
                
                SensorData.objects.create(
                    tank=tank,
                    timestamp=current_time,
                    water_level_percentage=water_level,
                    water_level_inches=water_level * tank.capacity_gallons / 1000,  # Rough conversion
                    water_temperature_f=water_temp,
                    ambient_temperature_f=water_temp + random.uniform(-5, 10),
                    ph_level=ph_level,
                    turbidity_ntu=random.uniform(0.1, 2.0),
                    dissolved_oxygen_ppm=random.uniform(6.0, 12.0),
                    conductivity_us_cm=random.uniform(200, 800),
                    flow_rate_gpm=random.uniform(0, 50) if random.random() > 0.7 else 0,
                    signal_strength=random.randint(70, 100),
                    battery_voltage=random.uniform(3.2, 4.2),
                    is_valid=random.random() > 0.05,  # 95% valid data
                )
                
                current_time += timedelta(hours=1)
        
        # Create some sample alerts
        self.stdout.write('Creating sample alerts...')
        alert_data = [
            {
                'tank': tanks[0],
                'alert_type': 'low_level',
                'severity': 'high',
                'title': 'Low Water Level Alert',
                'message': 'Water level has dropped below 20% capacity.',
                'threshold_value': 20.0,
                'actual_value': 15.5,
            },
            {
                'tank': tanks[1],
                'alert_type': 'temperature',
                'severity': 'medium',
                'title': 'High Temperature Alert',
                'message': 'Water temperature is above normal range.',
                'threshold_value': 70.0,
                'actual_value': 75.2,
            },
            {
                'tank': tanks[2],
                'alert_type': 'sensor_offline',
                'severity': 'critical',
                'title': 'Sensor Communication Lost',
                'message': 'pH sensor has not reported data for over 2 hours.',
                'threshold_value': None,
                'actual_value': None,
            },
        ]
        
        for alert_info in alert_data:
            Alert.objects.create(
                **alert_info,
                created_at=timezone.now() - timedelta(hours=random.randint(1, 48)),
                status=random.choice(['active', 'active', 'acknowledged']),
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- {len(tanks)} water tanks\n'
                f'- {Sensor.objects.count()} sensors\n'
                f'- {SensorData.objects.count()} sensor readings\n'
                f'- {Alert.objects.count()} alerts'
            )
        ) 
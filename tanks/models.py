from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class WaterTank(models.Model):
    """Model representing a water tank in NYC"""
    
    TANK_STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('offline', 'Offline'),
        ('error', 'Error'),
    ]
    
    TANK_TYPE_CHOICES = [
        ('rooftop', 'Rooftop Tank'),
        ('basement', 'Basement Tank'),
        ('ground', 'Ground Level Tank'),
        ('elevated', 'Elevated Tank'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=500, help_text="Full address or location description")
    borough = models.CharField(max_length=50, choices=[
        ('manhattan', 'Manhattan'),
        ('brooklyn', 'Brooklyn'),
        ('queens', 'Queens'),
        ('bronx', 'Bronx'),
        ('staten_island', 'Staten Island'),
    ])
    tank_type = models.CharField(max_length=20, choices=TANK_TYPE_CHOICES, default='rooftop')
    capacity_gallons = models.PositiveIntegerField(help_text="Tank capacity in gallons")
    installation_date = models.DateField()
    status = models.CharField(max_length=20, choices=TANK_STATUS_CHOICES, default='active')
    
    # Building information
    building_name = models.CharField(max_length=200, blank=True)
    building_owner = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # GPS coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} - {self.location}"
    
    @property
    def latest_sensor_data(self):
        """Get the most recent sensor reading"""
        return self.sensor_data.order_by('-timestamp').first()
    
    @property
    def connection_status(self):
        """Check if tank is connected based on recent data"""
        latest_data = self.latest_sensor_data
        if not latest_data:
            return 'disconnected'
        
        # Consider connected if data is less than 30 minutes old
        time_diff = timezone.now() - latest_data.timestamp
        if time_diff.total_seconds() < 1800:  # 30 minutes
            return 'connected'
        else:
            return 'disconnected'
    
    @property
    def current_water_level_percentage(self):
        """Get current water level as percentage"""
        latest_data = self.latest_sensor_data
        if latest_data and latest_data.water_level_percentage is not None:
            return latest_data.water_level_percentage
        return None


class Sensor(models.Model):
    """Model representing sensors installed in water tanks"""
    
    SENSOR_TYPE_CHOICES = [
        ('level', 'Water Level Sensor'),
        ('temperature', 'Temperature Sensor'),
        ('ph', 'pH Sensor'),
        ('turbidity', 'Turbidity Sensor'),
        ('dissolved_oxygen', 'Dissolved Oxygen Sensor'),
        ('conductivity', 'Conductivity Sensor'),
        ('flow', 'Flow Rate Sensor'),
    ]
    
    SENSOR_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('error', 'Error'),
        ('low_battery', 'Low Battery'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tank = models.ForeignKey(WaterTank, on_delete=models.CASCADE, related_name='sensors')
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPE_CHOICES)
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    installation_date = models.DateField()
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SENSOR_STATUS_CHOICES, default='active')
    battery_level = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True,
        help_text="Battery level percentage"
    )
    
    # Calibration data
    last_calibration = models.DateTimeField(null=True, blank=True)
    calibration_offset = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['tank', 'sensor_type']
        unique_together = ['tank', 'sensor_type']
        
    def __str__(self):
        return f"{self.tank.name} - {self.get_sensor_type_display()}"


class SensorData(models.Model):
    """Model storing sensor readings and measurements"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tank = models.ForeignKey(WaterTank, on_delete=models.CASCADE, related_name='sensor_data')
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Water level measurements
    water_level_inches = models.FloatField(null=True, blank=True, help_text="Water level in inches")
    water_level_percentage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Water level as percentage of tank capacity"
    )
    
    # Temperature measurements
    water_temperature_f = models.FloatField(null=True, blank=True, help_text="Water temperature in Fahrenheit")
    ambient_temperature_f = models.FloatField(null=True, blank=True, help_text="Ambient temperature in Fahrenheit")
    
    # Water quality measurements
    ph_level = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(14)],
        help_text="pH level (0-14)"
    )
    turbidity_ntu = models.FloatField(null=True, blank=True, help_text="Turbidity in NTU")
    dissolved_oxygen_ppm = models.FloatField(null=True, blank=True, help_text="Dissolved oxygen in ppm")
    conductivity_us_cm = models.FloatField(null=True, blank=True, help_text="Conductivity in µS/cm")
    
    # Flow measurements
    flow_rate_gpm = models.FloatField(null=True, blank=True, help_text="Flow rate in gallons per minute")
    total_flow_gallons = models.FloatField(null=True, blank=True, help_text="Total flow in gallons")
    
    # System measurements
    signal_strength = models.IntegerField(null=True, blank=True, help_text="Signal strength percentage")
    battery_voltage = models.FloatField(null=True, blank=True, help_text="Battery voltage")
    
    # Data quality flags
    is_valid = models.BooleanField(default=True)
    quality_flags = models.JSONField(default=dict, blank=True, help_text="Data quality indicators")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tank', '-timestamp']),
            models.Index(fields=['sensor', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        
    def __str__(self):
        return f"{self.tank.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def water_temperature_c(self):
        """Convert Fahrenheit to Celsius"""
        if self.water_temperature_f is not None:
            return (self.water_temperature_f - 32) * 5/9
        return None


class Alert(models.Model):
    """Model for storing alerts and notifications"""
    
    ALERT_TYPE_CHOICES = [
        ('low_level', 'Low Water Level'),
        ('high_level', 'High Water Level'),
        ('temperature', 'Temperature Alert'),
        ('ph', 'pH Alert'),
        ('turbidity', 'Turbidity Alert'),
        ('sensor_offline', 'Sensor Offline'),
        ('low_battery', 'Low Battery'),
        ('maintenance_due', 'Maintenance Due'),
        ('data_anomaly', 'Data Anomaly'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tank = models.ForeignKey(WaterTank, on_delete=models.CASCADE, related_name='alerts')
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    threshold_value = models.FloatField(null=True, blank=True)
    actual_value = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.tank.name} - {self.title}"

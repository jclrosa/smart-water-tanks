from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import WaterTank, Sensor, SensorData, Alert


@admin.register(WaterTank)
class WaterTankAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'borough', 'tank_type', 'capacity_gallons', 
        'status', 'connection_status_display', 'current_level_display',
        'created_at'
    ]
    list_filter = ['borough', 'tank_type', 'status', 'created_at']
    search_fields = ['name', 'location', 'building_name', 'building_owner']
    readonly_fields = ['id', 'created_at', 'updated_at', 'connection_status_display', 'current_level_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'location', 'borough', 'tank_type', 'capacity_gallons', 'status')
        }),
        ('Building Information', {
            'fields': ('building_name', 'building_owner', 'contact_email', 'contact_phone')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Dates', {
            'fields': ('installation_date', 'created_at', 'updated_at')
        }),
        ('Current Status', {
            'fields': ('connection_status_display', 'current_level_display')
        }),
        ('Metadata', {
            'fields': ('created_by',)
        })
    )
    
    def connection_status_display(self, obj):
        status = obj.connection_status
        color = {
            'connected': 'green',
            'disconnected': 'red',
        }.get(status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status.title()
        )
    connection_status_display.short_description = 'Connection Status'
    
    def current_level_display(self, obj):
        level = obj.current_water_level_percentage
        if level is not None:
            color = 'green' if level > 50 else 'orange' if level > 20 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color,
                round(level, 1)
            )
        return format_html('<span style="color: gray;">No Data</span>')
    current_level_display.short_description = 'Current Level'


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = [
        'tank', 'sensor_type', 'model_number', 'serial_number',
        'status', 'battery_level_display', 'installation_date'
    ]
    list_filter = ['sensor_type', 'status', 'installation_date']
    search_fields = ['tank__name', 'model_number', 'serial_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tank', 'sensor_type', 'model_number', 'serial_number', 'status')
        }),
        ('Dates', {
            'fields': ('installation_date', 'last_maintenance', 'next_maintenance', 'created_at', 'updated_at')
        }),
        ('Battery & Calibration', {
            'fields': ('battery_level', 'last_calibration', 'calibration_offset')
        })
    )
    
    def battery_level_display(self, obj):
        if obj.battery_level is not None:
            color = 'green' if obj.battery_level > 50 else 'orange' if obj.battery_level > 20 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color,
                obj.battery_level
            )
        return format_html('<span style="color: gray;">N/A</span>')
    battery_level_display.short_description = 'Battery Level'


@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = [
        'tank', 'timestamp', 'water_level_percentage', 'water_temperature_f',
        'ph_level', 'signal_strength', 'is_valid'
    ]
    list_filter = ['tank', 'is_valid', 'timestamp']
    search_fields = ['tank__name']
    readonly_fields = ['id', 'created_at', 'water_temperature_c']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tank', 'sensor', 'timestamp', 'is_valid', 'created_at')
        }),
        ('Water Level', {
            'fields': ('water_level_inches', 'water_level_percentage')
        }),
        ('Temperature', {
            'fields': ('water_temperature_f', 'water_temperature_c', 'ambient_temperature_f')
        }),
        ('Water Quality', {
            'fields': ('ph_level', 'turbidity_ntu', 'dissolved_oxygen_ppm', 'conductivity_us_cm')
        }),
        ('Flow', {
            'fields': ('flow_rate_gpm', 'total_flow_gallons')
        }),
        ('System', {
            'fields': ('signal_strength', 'battery_voltage')
        }),
        ('Quality Control', {
            'fields': ('quality_flags',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tank', 'sensor')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'tank', 'alert_type', 'severity', 'status', 'title',
        'created_at', 'acknowledged_by', 'resolved_by'
    ]
    list_filter = ['alert_type', 'severity', 'status', 'created_at']
    search_fields = ['tank__name', 'title', 'message']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tank', 'sensor', 'alert_type', 'severity', 'status')
        }),
        ('Alert Details', {
            'fields': ('title', 'message', 'threshold_value', 'actual_value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'acknowledged_at', 'resolved_at')
        }),
        ('Actions', {
            'fields': ('acknowledged_by', 'resolved_by')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tank', 'sensor', 'acknowledged_by', 'resolved_by')


# Customize admin site header
admin.site.site_header = "Smart Water Tanks Administration"
admin.site.site_title = "Smart Water Tanks Admin"
admin.site.index_title = "Welcome to Smart Water Tanks Administration"

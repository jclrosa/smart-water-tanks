from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
import json
import csv
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import pandas as pd

from tanks.models import WaterTank, SensorData, Alert


@login_required
def dashboard_home(request):
    """Main dashboard view with overview statistics"""
    
    # Get basic statistics
    total_tanks = WaterTank.objects.count()
    active_tanks = WaterTank.objects.filter(status='active').count()
    
    # Get tanks with recent data (connected)
    recent_threshold = timezone.now() - timedelta(minutes=30)
    connected_tanks = WaterTank.objects.filter(
        sensor_data__timestamp__gte=recent_threshold
    ).distinct().count()
    
    # Get active alerts
    active_alerts = Alert.objects.filter(status='active').count()
    critical_alerts = Alert.objects.filter(
        status='active', 
        severity='critical'
    ).count()
    
    # Get recent sensor data for charts
    recent_data = SensorData.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).select_related('tank')
    
    # Borough distribution
    borough_data = WaterTank.objects.values('borough').annotate(
        count=Count('id')
    ).order_by('borough')
    
    # Tank status distribution
    status_data = WaterTank.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Recent alerts
    recent_alerts = Alert.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('tank').order_by('-created_at')[:10]
    
    # Generate charts
    charts = generate_dashboard_charts()
    
    context = {
        'total_tanks': total_tanks,
        'active_tanks': active_tanks,
        'connected_tanks': connected_tanks,
        'active_alerts': active_alerts,
        'critical_alerts': critical_alerts,
        'borough_data': list(borough_data),
        'status_data': list(status_data),
        'recent_alerts': recent_alerts,
        'charts': charts,
    }
    
    return render(request, 'dashboard/home.html', context)


def generate_dashboard_charts():
    """Generate charts for dashboard"""
    charts = {}
    
    # 1. Water Level Trends (Last 24 hours)
    last_24h = timezone.now() - timedelta(hours=24)
    water_level_data = SensorData.objects.filter(
        timestamp__gte=last_24h,
        water_level_percentage__isnull=False
    ).select_related('tank').order_by('timestamp')
    
    if water_level_data.exists():
        # Group by tank
        tank_data = {}
        for reading in water_level_data:
            tank_name = reading.tank.name
            if tank_name not in tank_data:
                tank_data[tank_name] = {'timestamps': [], 'levels': []}
            tank_data[tank_name]['timestamps'].append(reading.timestamp)
            tank_data[tank_name]['levels'].append(reading.water_level_percentage)
        
        fig = go.Figure()
        for tank_name, data in tank_data.items():
            fig.add_trace(go.Scatter(
                x=data['timestamps'],
                y=data['levels'],
                mode='lines+markers',
                name=tank_name,
                line=dict(width=2),
                marker=dict(size=4)
            ))
        
        fig.update_layout(
            title='Water Level Trends (Last 24 Hours)',
            xaxis_title='Time',
            yaxis_title='Water Level (%)',
            height=400,
            showlegend=True,
            hovermode='x unified'
        )
        charts['water_levels'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # 2. Temperature Distribution
    temp_data = SensorData.objects.filter(
        timestamp__gte=last_24h,
        water_temperature_f__isnull=False
    ).values_list('water_temperature_f', flat=True)
    
    if temp_data:
        fig = go.Figure(data=[go.Histogram(
            x=list(temp_data),
            nbinsx=20,
            marker_color='lightblue',
            opacity=0.7
        )])
        fig.update_layout(
            title='Water Temperature Distribution (Last 24 Hours)',
            xaxis_title='Temperature (°F)',
            yaxis_title='Frequency',
            height=300
        )
        charts['temperature_dist'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # 3. Borough Tank Distribution (Pie Chart)
    borough_counts = WaterTank.objects.values('borough').annotate(
        count=Count('id')
    ).order_by('borough')
    
    if borough_counts:
        labels = [item['borough'].title() for item in borough_counts]
        values = [item['count'] for item in borough_counts]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
        )])
        fig.update_layout(
            title='Tank Distribution by Borough',
            height=350
        )
        charts['borough_pie'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # 4. Alert Severity Over Time
    alert_data = Alert.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).values('created_at__date', 'severity').annotate(count=Count('id'))
    
    if alert_data:
        df = pd.DataFrame(list(alert_data))
        df['created_at__date'] = pd.to_datetime(df['created_at__date'])
        
        fig = px.bar(
            df, 
            x='created_at__date', 
            y='count', 
            color='severity',
            title='Alert Trends (Last 7 Days)',
            color_discrete_map={
                'low': '#10B981',
                'medium': '#F59E0B', 
                'high': '#EF4444',
                'critical': '#DC2626'
            }
        )
        fig.update_layout(height=350)
        charts['alerts_trend'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    return charts


class TankListView(LoginRequiredMixin, ListView):
    """List view for all water tanks"""
    model = WaterTank
    template_name = 'dashboard/tank_list.html'
    context_object_name = 'tanks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = WaterTank.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(location__icontains=search) |
                Q(building_name__icontains=search)
            )
        
        # Filter by borough
        borough = self.request.GET.get('borough')
        if borough:
            queryset = queryset.filter(borough=borough)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('name')


class TankDetailView(LoginRequiredMixin, DetailView):
    """Detail view for individual water tank"""
    model = WaterTank
    template_name = 'dashboard/tank_detail.html'
    context_object_name = 'tank'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tank = self.object
        
        # Get recent sensor data (last 7 days)
        recent_data = SensorData.objects.filter(
            tank=tank,
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).order_by('-timestamp')
        
        # Get latest reading
        latest_reading = recent_data.first()
        
        # Get active alerts
        active_alerts = Alert.objects.filter(
            tank=tank,
            status='active'
        ).order_by('-created_at')
        
        # Get sensors
        sensors = tank.sensors.all()
        
        # Generate tank-specific charts
        charts = generate_tank_charts(tank)
        
        context.update({
            'latest_reading': latest_reading,
            'active_alerts': active_alerts,
            'sensors': sensors,
            'recent_data_count': recent_data.count(),
            'charts': charts,
        })
        
        return context


def generate_tank_charts(tank):
    """Generate charts for individual tank detail view"""
    charts = {}
    
    # Get data for last 7 days
    last_7_days = timezone.now() - timedelta(days=7)
    sensor_data = SensorData.objects.filter(
        tank=tank,
        timestamp__gte=last_7_days
    ).order_by('timestamp')
    
    if not sensor_data.exists():
        return charts
    
    # Convert to lists for plotting
    timestamps = [reading.timestamp for reading in sensor_data]
    
    # 1. Water Level Trend
    water_levels = [reading.water_level_percentage for reading in sensor_data if reading.water_level_percentage is not None]
    water_timestamps = [reading.timestamp for reading in sensor_data if reading.water_level_percentage is not None]
    
    if water_levels:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=water_timestamps,
            y=water_levels,
            mode='lines+markers',
            name='Water Level',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=6),
            fill='tonexty',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        
        # Add threshold lines
        fig.add_hline(y=20, line_dash="dash", line_color="red", 
                     annotation_text="Low Level Alert (20%)")
        fig.add_hline(y=80, line_dash="dash", line_color="orange", 
                     annotation_text="High Level Warning (80%)")
        
        fig.update_layout(
            title=f'Water Level Trend - {tank.name}',
            xaxis_title='Time',
            yaxis_title='Water Level (%)',
            height=400,
            yaxis=dict(range=[0, 100])
        )
        charts['water_level'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # 2. Temperature Trend
    temperatures = [reading.water_temperature_f for reading in sensor_data if reading.water_temperature_f is not None]
    temp_timestamps = [reading.timestamp for reading in sensor_data if reading.water_temperature_f is not None]
    
    if temperatures:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=temp_timestamps,
            y=temperatures,
            mode='lines+markers',
            name='Water Temperature',
            line=dict(color='#EF4444', width=2),
            marker=dict(size=4)
        ))
        
        fig.update_layout(
            title=f'Water Temperature Trend - {tank.name}',
            xaxis_title='Time',
            yaxis_title='Temperature (°F)',
            height=350
        )
        charts['temperature'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # 3. pH Level Trend
    ph_levels = [reading.ph_level for reading in sensor_data if reading.ph_level is not None]
    ph_timestamps = [reading.timestamp for reading in sensor_data if reading.ph_level is not None]
    
    if ph_levels:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ph_timestamps,
            y=ph_levels,
            mode='lines+markers',
            name='pH Level',
            line=dict(color='#10B981', width=2),
            marker=dict(size=4)
        ))
        
        # Add pH range indicators
        fig.add_hline(y=6.5, line_dash="dash", line_color="orange", 
                     annotation_text="Min Safe pH (6.5)")
        fig.add_hline(y=8.5, line_dash="dash", line_color="orange", 
                     annotation_text="Max Safe pH (8.5)")
        
        fig.update_layout(
            title=f'pH Level Trend - {tank.name}',
            xaxis_title='Time',
            yaxis_title='pH Level',
            height=350,
            yaxis=dict(range=[0, 14])
        )
        charts['ph_level'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # 4. Multi-parameter Chart
    fig = go.Figure()
    
    # Water quality parameters on secondary y-axis
    if ph_levels:
        fig.add_trace(go.Scatter(
            x=ph_timestamps,
            y=ph_levels,
            mode='lines',
            name='pH Level',
            yaxis='y2',
            line=dict(color='#10B981')
        ))
    
    turbidity_levels = [reading.turbidity_ntu for reading in sensor_data if reading.turbidity_ntu is not None]
    turbidity_timestamps = [reading.timestamp for reading in sensor_data if reading.turbidity_ntu is not None]
    
    if turbidity_levels:
        fig.add_trace(go.Scatter(
            x=turbidity_timestamps,
            y=turbidity_levels,
            mode='lines',
            name='Turbidity (NTU)',
            yaxis='y3',
            line=dict(color='#F59E0B')
        ))
    
    if water_levels:
        fig.add_trace(go.Scatter(
            x=water_timestamps,
            y=water_levels,
            mode='lines',
            name='Water Level (%)',
            line=dict(color='#3B82F6')
        ))
    
    fig.update_layout(
        title=f'Multi-Parameter Monitoring - {tank.name}',
        xaxis_title='Time',
        height=400,
        yaxis=dict(title='Water Level (%)', side='left'),
        yaxis2=dict(title='pH Level', side='right', overlaying='y', range=[0, 14]),
        yaxis3=dict(title='Turbidity (NTU)', side='right', overlaying='y', position=0.95),
        legend=dict(x=0, y=1)
    )
    charts['multi_param'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # 5. Signal Strength and Battery Status
    signal_data = [reading.signal_strength for reading in sensor_data if reading.signal_strength is not None]
    signal_timestamps = [reading.timestamp for reading in sensor_data if reading.signal_strength is not None]
    
    if signal_data:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=signal_timestamps,
            y=signal_data,
            mode='lines+markers',
            name='Signal Strength',
            line=dict(color='#8B5CF6', width=2),
            marker=dict(size=4)
        ))
        
        fig.add_hline(y=30, line_dash="dash", line_color="red", 
                     annotation_text="Poor Signal (30%)")
        fig.add_hline(y=70, line_dash="dash", line_color="orange", 
                     annotation_text="Good Signal (70%)")
        
        fig.update_layout(
            title=f'Signal Strength - {tank.name}',
            xaxis_title='Time',
            yaxis_title='Signal Strength (%)',
            height=300,
            yaxis=dict(range=[0, 100])
        )
        charts['signal_strength'] = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    return charts


@login_required
def tank_data_api(request, tank_id):
    """API endpoint for tank data (for AJAX updates)"""
    tank = get_object_or_404(WaterTank, id=tank_id)
    latest_data = tank.latest_sensor_data
    
    if latest_data:
        data = {
            'water_level': latest_data.water_level_percentage,
            'temperature': latest_data.water_temperature_f,
            'ph': latest_data.ph_level,
            'timestamp': latest_data.timestamp.isoformat(),
            'connection_status': tank.connection_status,
        }
    else:
        data = {
            'water_level': None,
            'temperature': None,
            'ph': None,
            'timestamp': None,
            'connection_status': 'disconnected',
        }
    
    return JsonResponse(data)


@login_required
def export_tank_data(request, tank_id):
    """Export tank data as CSV"""
    tank = get_object_or_404(WaterTank, id=tank_id)
    
    # Get date range from request
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get sensor data
    sensor_data = SensorData.objects.filter(
        tank=tank,
        timestamp__gte=start_date
    ).order_by('-timestamp')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{tank.name}_data_{days}days.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Timestamp', 'Water Level (%)', 'Water Level (inches)', 
        'Water Temperature (°F)', 'pH Level', 'Turbidity (NTU)',
        'Dissolved Oxygen (ppm)', 'Conductivity (µS/cm)',
        'Flow Rate (GPM)', 'Signal Strength (%)'
    ])
    
    for data in sensor_data:
        writer.writerow([
            data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            data.water_level_percentage,
            data.water_level_inches,
            data.water_temperature_f,
            data.ph_level,
            data.turbidity_ntu,
            data.dissolved_oxygen_ppm,
            data.conductivity_us_cm,
            data.flow_rate_gpm,
            data.signal_strength,
        ])
    
    return response


@login_required
def alerts_view(request):
    """View for managing alerts"""
    alerts = Alert.objects.all().select_related('tank', 'sensor')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        alerts = alerts.filter(status=status)
    
    # Filter by severity
    severity = request.GET.get('severity')
    if severity:
        alerts = alerts.filter(severity=severity)
    
    # Filter by tank
    tank_id = request.GET.get('tank')
    if tank_id:
        alerts = alerts.filter(tank_id=tank_id)
    
    alerts = alerts.order_by('-created_at')
    
    context = {
        'alerts': alerts,
        'tanks': WaterTank.objects.all().order_by('name'),
        'current_filters': {
            'status': status or '',
            'severity': severity or '',
            'tank': tank_id or '',
        }
    }
    
    return render(request, 'dashboard/alerts.html', context)


@login_required
def dashboard_data_api(request):
    """API endpoint for real-time dashboard updates"""
    # Get basic statistics
    total_tanks = WaterTank.objects.count()
    active_tanks = WaterTank.objects.filter(status='active').count()
    
    # Get tanks with recent data (connected)
    recent_threshold = timezone.now() - timedelta(minutes=30)
    connected_tanks = WaterTank.objects.filter(
        sensor_data__timestamp__gte=recent_threshold
    ).distinct().count()
    
    # Get active alerts
    active_alerts = Alert.objects.filter(status='active').count()
    critical_alerts = Alert.objects.filter(
        status='active', 
        severity='critical'
    ).count()
    
    # Get recent sensor readings for live updates
    recent_readings = []
    for tank in WaterTank.objects.filter(status='active')[:5]:
        latest_data = tank.latest_sensor_data
        if latest_data:
            recent_readings.append({
                'tank_id': str(tank.id),
                'tank_name': tank.name,
                'water_level': latest_data.water_level_percentage,
                'temperature': latest_data.water_temperature_f,
                'ph_level': latest_data.ph_level,
                'timestamp': latest_data.timestamp.isoformat(),
                'connection_status': tank.connection_status,
            })
    
    # Get latest alerts
    latest_alerts = []
    for alert in Alert.objects.filter(status='active').order_by('-created_at')[:5]:
        latest_alerts.append({
            'id': str(alert.id),
            'tank_name': alert.tank.name,
            'title': alert.title,
            'severity': alert.severity,
            'created_at': alert.created_at.isoformat(),
        })
    
    data = {
        'statistics': {
            'total_tanks': total_tanks,
            'active_tanks': active_tanks,
            'connected_tanks': connected_tanks,
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts,
        },
        'recent_readings': recent_readings,
        'latest_alerts': latest_alerts,
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(data)


@login_required
def tank_chart_data_api(request, tank_id):
    """API endpoint for tank chart data updates"""
    tank = get_object_or_404(WaterTank, id=tank_id)
    
    # Get hours parameter (default 24)
    hours = int(request.GET.get('hours', 24))
    start_time = timezone.now() - timedelta(hours=hours)
    
    # Get sensor data
    sensor_data = SensorData.objects.filter(
        tank=tank,
        timestamp__gte=start_time
    ).order_by('timestamp')
    
    # Prepare data for charts
    chart_data = {
        'timestamps': [reading.timestamp.isoformat() for reading in sensor_data],
        'water_levels': [reading.water_level_percentage for reading in sensor_data if reading.water_level_percentage is not None],
        'temperatures': [reading.water_temperature_f for reading in sensor_data if reading.water_temperature_f is not None],
        'ph_levels': [reading.ph_level for reading in sensor_data if reading.ph_level is not None],
        'signal_strength': [reading.signal_strength for reading in sensor_data if reading.signal_strength is not None],
    }
    
    return JsonResponse(chart_data)

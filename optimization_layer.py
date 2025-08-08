#!/usr/bin/env python3
"""
Angles AI Universe™ Optimization Layer
Performance monitoring and optimization with intelligent resource management

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import sys
import time
import json
import psutil
import logging
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import threading
import queue
import functools

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from alerts.notify import AlertManager
except ImportError:
    AlertManager = None

class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.setup_logging()
        self.alert_manager = AlertManager() if AlertManager else None
        
        # Performance configuration
        self.config = {
            'monitoring_interval': 60,  # seconds
            'performance_history_size': 1000,
            'cpu_threshold_warning': 80,  # %
            'cpu_threshold_critical': 95,  # %
            'memory_threshold_warning': 85,  # %
            'memory_threshold_critical': 95,  # %
            'disk_threshold_warning': 85,  # %
            'disk_threshold_critical': 95,  # %
            'response_time_threshold': 5000,  # ms
            'optimization_frequency': 3600,  # seconds (1 hour)
            'auto_optimization': True
        }
        
        # Performance metrics storage
        self.metrics_queue = queue.Queue(maxsize=self.config['performance_history_size'])
        self.current_metrics = {}
        self.performance_history = []
        self.optimization_suggestions = []
        
        # Task performance tracking
        self.task_metrics = {}
        self.slow_tasks = {}
        
        # Threading
        self.monitoring_thread = None
        self.optimization_thread = None
        self.stop_event = threading.Event()
        
        self.logger.info("⚡ Angles AI Universe™ Optimization Layer Initialized")
    
    def setup_logging(self):
        """Setup logging for optimization layer"""
        os.makedirs("logs/optimization", exist_ok=True)
        
        self.logger = logging.getLogger('optimization_layer')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        log_file = "logs/optimization/optimization.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def performance_monitor(self, func_name: Optional[str] = None):
        """Decorator to monitor function performance"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                task_name = func_name or func.__name__
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                success = False
                error = None
                result = None
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss
                    
                    duration = (end_time - start_time) * 1000  # ms
                    memory_delta = end_memory - start_memory
                    
                    # Record task performance
                    self.record_task_performance(task_name, {
                        'duration_ms': duration,
                        'memory_delta_bytes': memory_delta,
                        'success': success,
                        'error': error,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                
                return result
            return wrapper
        return decorator
    
    def record_task_performance(self, task_name: str, metrics: Dict[str, Any]):
        """Record performance metrics for a task"""
        if task_name not in self.task_metrics:
            self.task_metrics[task_name] = {
                'runs': 0,
                'total_duration': 0,
                'total_memory_delta': 0,
                'successes': 0,
                'failures': 0,
                'average_duration': 0,
                'max_duration': 0,
                'min_duration': float('inf'),
                'recent_runs': []
            }
        
        stats = self.task_metrics[task_name]
        duration = metrics['duration_ms']
        
        # Update basic stats
        stats['runs'] += 1
        stats['total_duration'] += duration
        stats['total_memory_delta'] += metrics['memory_delta_bytes']
        
        if metrics['success']:
            stats['successes'] += 1
        else:
            stats['failures'] += 1
        
        # Update duration stats
        stats['average_duration'] = stats['total_duration'] / stats['runs']
        stats['max_duration'] = max(stats['max_duration'], duration)
        stats['min_duration'] = min(stats['min_duration'], duration)
        
        # Keep recent runs (last 10)
        stats['recent_runs'].append(metrics)
        if len(stats['recent_runs']) > 10:
            stats['recent_runs'].pop(0)
        
        # Check for slow tasks
        if duration > self.config['response_time_threshold']:
            self.flag_slow_task(task_name, metrics)
        
        self.logger.debug(f"📊 Task {task_name}: {duration:.1f}ms")
    
    def flag_slow_task(self, task_name: str, metrics: Dict[str, Any]):
        """Flag and analyze slow tasks"""
        if task_name not in self.slow_tasks:
            self.slow_tasks[task_name] = []
        
        self.slow_tasks[task_name].append(metrics)
        
        # Keep only recent slow runs (last 5)
        if len(self.slow_tasks[task_name]) > 5:
            self.slow_tasks[task_name].pop(0)
        
        self.logger.warning(f"🐌 Slow task detected: {task_name} took {metrics['duration_ms']:.1f}ms")
        
        # Generate optimization suggestion
        suggestion = self.analyze_slow_task(task_name, metrics)
        if suggestion:
            self.optimization_suggestions.append(suggestion)
    
    def analyze_slow_task(self, task_name: str, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze slow task and generate optimization suggestion"""
        duration = metrics['duration_ms']
        memory_delta = metrics['memory_delta_bytes']
        
        suggestions = []
        
        # High duration analysis
        if duration > 10000:  # 10+ seconds
            suggestions.append("Consider breaking this task into smaller chunks")
            suggestions.append("Check for network timeouts or database locks")
        elif duration > 5000:  # 5+ seconds
            suggestions.append("Optimize database queries or API calls")
            suggestions.append("Consider caching frequently accessed data")
        
        # High memory usage
        if memory_delta > 100 * 1024 * 1024:  # 100MB+
            suggestions.append("Memory usage is high - check for memory leaks")
            suggestions.append("Consider streaming large data sets instead of loading all at once")
        
        # Task-specific suggestions
        if 'backup' in task_name.lower():
            suggestions.append("Consider incremental backups for large datasets")
            suggestions.append("Use compression to reduce backup size")
        elif 'sync' in task_name.lower():
            suggestions.append("Implement batch processing for sync operations")
            suggestions.append("Add progress tracking for long sync operations")
        elif 'health' in task_name.lower():
            suggestions.append("Reduce health check scope or frequency")
            suggestions.append("Parallelize independent health checks")
        
        if suggestions:
            return {
                'task_name': task_name,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'duration_ms': duration,
                'memory_delta_mb': memory_delta / (1024 * 1024),
                'suggestions': suggestions,
                'severity': 'high' if duration > 10000 else 'medium'
            }
        
        return None
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('.')
            
            # Network metrics (basic)
            network = psutil.net_io_counters()
            
            metrics = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg_1m': load_avg[0],
                    'load_avg_5m': load_avg[1],
                    'load_avg_15m': load_avg[2]
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_percent': memory.percent,
                    'swap_total_gb': swap.total / (1024**3),
                    'swap_used_percent': swap.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'used_percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            }
            
            return metrics
        
        except Exception as e:
            self.logger.error(f"❌ Failed to collect system metrics: {e}")
            return {}
    
    def analyze_system_health(self, metrics: Dict[str, Any]) -> List[str]:
        """Analyze system health and generate alerts"""
        alerts = []
        
        if not metrics:
            return ['Failed to collect system metrics']
        
        # CPU analysis
        cpu_percent = metrics.get('cpu', {}).get('percent', 0)
        if cpu_percent >= self.config['cpu_threshold_critical']:
            alerts.append(f"🚨 Critical CPU usage: {cpu_percent:.1f}%")
        elif cpu_percent >= self.config['cpu_threshold_warning']:
            alerts.append(f"⚠️ High CPU usage: {cpu_percent:.1f}%")
        
        # Memory analysis
        memory_percent = metrics.get('memory', {}).get('used_percent', 0)
        if memory_percent >= self.config['memory_threshold_critical']:
            alerts.append(f"🚨 Critical memory usage: {memory_percent:.1f}%")
        elif memory_percent >= self.config['memory_threshold_warning']:
            alerts.append(f"⚠️ High memory usage: {memory_percent:.1f}%")
        
        # Disk analysis
        disk_percent = metrics.get('disk', {}).get('used_percent', 0)
        if disk_percent >= self.config['disk_threshold_critical']:
            alerts.append(f"🚨 Critical disk usage: {disk_percent:.1f}%")
        elif disk_percent >= self.config['disk_threshold_warning']:
            alerts.append(f"⚠️ High disk usage: {disk_percent:.1f}%")
        
        # Load average analysis
        load_avg_1m = metrics.get('cpu', {}).get('load_avg_1m', 0)
        cpu_count = metrics.get('cpu', {}).get('count', 1)
        load_ratio = load_avg_1m / cpu_count
        
        if load_ratio > 2.0:
            alerts.append(f"🚨 High system load: {load_avg_1m:.2f} (ratio: {load_ratio:.2f})")
        elif load_ratio > 1.5:
            alerts.append(f"⚠️ Elevated system load: {load_avg_1m:.2f} (ratio: {load_ratio:.2f})")
        
        return alerts
    
    def generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on performance data"""
        recommendations = []
        
        # Analyze task performance
        for task_name, stats in self.task_metrics.items():
            if stats['runs'] < 5:  # Not enough data
                continue
            
            avg_duration = stats['average_duration']
            failure_rate = stats['failures'] / stats['runs'] if stats['runs'] > 0 else 0
            
            # Slow task recommendations
            if avg_duration > self.config['response_time_threshold']:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'task': task_name,
                    'issue': f"Average duration {avg_duration:.1f}ms exceeds threshold",
                    'recommendation': 'Consider optimizing this task or breaking it into smaller parts'
                })
            
            # High failure rate recommendations
            if failure_rate > 0.1:  # >10% failure rate
                recommendations.append({
                    'type': 'reliability',
                    'priority': 'high',
                    'task': task_name,
                    'issue': f"High failure rate: {failure_rate:.1%}",
                    'recommendation': 'Investigate error causes and improve error handling'
                })
        
        # System resource recommendations
        if self.performance_history:
            recent_metrics = self.performance_history[-10:]  # Last 10 measurements
            
            avg_cpu = statistics.mean(m.get('cpu', {}).get('percent', 0) for m in recent_metrics)
            avg_memory = statistics.mean(m.get('memory', {}).get('used_percent', 0) for m in recent_metrics)
            
            if avg_cpu > 70:
                recommendations.append({
                    'type': 'resource',
                    'priority': 'medium',
                    'issue': f"Average CPU usage is high: {avg_cpu:.1f}%",
                    'recommendation': 'Consider scaling up CPU resources or optimizing CPU-intensive tasks'
                })
            
            if avg_memory > 80:
                recommendations.append({
                    'type': 'resource',
                    'priority': 'medium',
                    'issue': f"Average memory usage is high: {avg_memory:.1f}%",
                    'recommendation': 'Consider increasing memory or optimizing memory usage'
                })
        
        return recommendations
    
    def apply_automatic_optimizations(self):
        """Apply automatic optimizations where safe"""
        self.logger.info("🔧 Applying automatic optimizations...")
        
        optimizations_applied = []
        
        try:
            # Clean up temporary files
            temp_files_cleaned = self.cleanup_temp_files()
            if temp_files_cleaned > 0:
                optimizations_applied.append(f"Cleaned {temp_files_cleaned} temporary files")
            
            # Optimize log files
            logs_optimized = self.optimize_log_files()
            if logs_optimized > 0:
                optimizations_applied.append(f"Optimized {logs_optimized} log files")
            
            # Clear caches if memory usage is high
            current_memory = psutil.virtual_memory().percent
            if current_memory > 85:
                self.clear_application_caches()
                optimizations_applied.append("Cleared application caches due to high memory usage")
            
            # Adjust task frequencies based on performance
            frequency_adjustments = self.adjust_task_frequencies()
            if frequency_adjustments:
                optimizations_applied.extend(frequency_adjustments)
            
            if optimizations_applied:
                self.logger.info("✅ Automatic optimizations applied:")
                for opt in optimizations_applied:
                    self.logger.info(f"   • {opt}")
            else:
                self.logger.info("ℹ️ No automatic optimizations needed")
        
        except Exception as e:
            self.logger.error(f"❌ Error applying automatic optimizations: {e}")
    
    def cleanup_temp_files(self) -> int:
        """Clean up temporary files"""
        import tempfile
        import glob
        
        temp_dir = tempfile.gettempdir()
        patterns = [
            'restore_temp_*',
            'backup_temp_*',
            'quicktest_*',
            '*.tmp'
        ]
        
        cleaned = 0
        for pattern in patterns:
            for file_path in glob.glob(os.path.join(temp_dir, pattern)):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned += 1
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                        cleaned += 1
                except:
                    pass
        
        return cleaned
    
    def optimize_log_files(self) -> int:
        """Optimize log files by archiving old ones"""
        import gzip
        
        optimized = 0
        cutoff_date = datetime.now() - timedelta(days=3)
        
        for root, dirs, files in os.walk('logs'):
            for file in files:
                if file.endswith('.log') and not file.endswith('.gz'):
                    file_path = os.path.join(root, file)
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        file_size = os.path.getsize(file_path)
                        
                        # Archive if old or large
                        if file_mtime < cutoff_date or file_size > 10 * 1024 * 1024:  # 10MB
                            with open(file_path, 'rb') as f_in:
                                with gzip.open(file_path + '.gz', 'wb') as f_out:
                                    f_out.writelines(f_in)
                            
                            os.remove(file_path)
                            optimized += 1
                    except:
                        pass
        
        return optimized
    
    def clear_application_caches(self):
        """Clear application caches to free memory"""
        # Clear any in-memory caches
        try:
            # Clear performance history to free memory
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-50:]
            
            # Clear old task metrics
            for task_name in list(self.task_metrics.keys()):
                if self.task_metrics[task_name]['runs'] == 0:
                    del self.task_metrics[task_name]
            
            self.logger.info("🧹 Cleared application caches")
        except Exception as e:
            self.logger.error(f"❌ Cache clearing failed: {e}")
    
    def adjust_task_frequencies(self) -> List[str]:
        """Adjust task frequencies based on performance"""
        adjustments = []
        
        # This would integrate with the scheduler to adjust frequencies
        # For now, just log recommendations
        
        for task_name, stats in self.task_metrics.items():
            if stats['runs'] < 5:
                continue
            
            avg_duration = stats['average_duration']
            failure_rate = stats['failures'] / stats['runs']
            
            # Suggest frequency adjustments
            if avg_duration > 10000 and failure_rate < 0.05:  # Slow but reliable
                adjustments.append(f"Consider reducing frequency of {task_name} (slow but reliable)")
            elif failure_rate > 0.2:  # High failure rate
                adjustments.append(f"Consider increasing retry interval for {task_name} (high failure rate)")
        
        return adjustments
    
    def start_monitoring(self):
        """Start the performance monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.stop_event.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("📊 Performance monitoring started")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self.stop_event.is_set():
            try:
                # Collect system metrics
                metrics = self.collect_system_metrics()
                if metrics:
                    self.current_metrics = metrics
                    self.performance_history.append(metrics)
                    
                    # Keep history size manageable
                    if len(self.performance_history) > self.config['performance_history_size']:
                        self.performance_history.pop(0)
                    
                    # Analyze health
                    alerts = self.analyze_system_health(metrics)
                    for alert in alerts:
                        self.logger.warning(alert)
                        
                        # Send critical alerts
                        if '🚨' in alert and self.alert_manager:
                            self.alert_manager.send_alert(
                                title="System Performance Alert",
                                message=alert,
                                severity="critical",
                                tags=['performance', 'system', 'optimization']
                            )
                
                # Wait for next iteration
                self.stop_event.wait(self.config['monitoring_interval'])
            
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                self.stop_event.wait(60)  # Wait before retrying
    
    def start_optimization(self):
        """Start the optimization thread"""
        if self.optimization_thread and self.optimization_thread.is_alive():
            return
        
        if not self.config['auto_optimization']:
            return
        
        self.optimization_thread = threading.Thread(target=self._optimization_loop)
        self.optimization_thread.daemon = True
        self.optimization_thread.start()
        
        self.logger.info("⚡ Auto-optimization started")
    
    def _optimization_loop(self):
        """Main optimization loop"""
        while not self.stop_event.is_set():
            try:
                self.apply_automatic_optimizations()
                
                # Generate and log recommendations
                recommendations = self.generate_optimization_recommendations()
                if recommendations:
                    self.logger.info(f"💡 Generated {len(recommendations)} optimization recommendations")
                    
                    # Save recommendations to file
                    self.save_optimization_report(recommendations)
                
                # Wait for next optimization cycle
                self.stop_event.wait(self.config['optimization_frequency'])
            
            except Exception as e:
                self.logger.error(f"❌ Optimization error: {e}")
                self.stop_event.wait(300)  # Wait 5 minutes before retrying
    
    def save_optimization_report(self, recommendations: List[Dict[str, Any]]):
        """Save optimization report to file"""
        try:
            report = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'recommendations': recommendations,
                'task_metrics': self.task_metrics,
                'optimization_suggestions': self.optimization_suggestions,
                'system_metrics': self.current_metrics
            }
            
            os.makedirs('logs/optimization', exist_ok=True)
            report_file = f"logs/optimization/optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"📋 Optimization report saved: {report_file}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save optimization report: {e}")
    
    def stop_monitoring(self):
        """Stop all monitoring and optimization"""
        self.stop_event.set()
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5)
        
        self.logger.info("🛑 Performance monitoring stopped")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            'current_metrics': self.current_metrics,
            'task_metrics': self.task_metrics,
            'optimization_suggestions': self.optimization_suggestions,
            'slow_tasks': self.slow_tasks,
            'recommendations': self.generate_optimization_recommendations()
        }

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def monitor_performance(func_name: Optional[str] = None):
    """Decorator to monitor function performance"""
    return get_performance_monitor().performance_monitor(func_name)

def main():
    """Main entry point for optimization layer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimization Layer')
    parser.add_argument('--start', action='store_true', help='Start performance monitoring')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    parser.add_argument('--optimize', action='store_true', help='Run optimization tasks')
    
    args = parser.parse_args()
    
    try:
        monitor = get_performance_monitor()
        
        if args.start:
            monitor.start_monitoring()
            monitor.start_optimization()
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                monitor.stop_monitoring()
        
        elif args.report:
            summary = monitor.get_performance_summary()
            print(json.dumps(summary, indent=2, default=str))
        
        elif args.optimize:
            monitor.apply_automatic_optimizations()
        
        else:
            # Default: show current performance
            if monitor.current_metrics:
                print("Current System Metrics:")
                print(json.dumps(monitor.current_metrics, indent=2, default=str))
            else:
                print("No performance data available. Run with --start to begin monitoring.")
    
    except KeyboardInterrupt:
        print("\n🛑 Optimization layer interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Optimization layer failure: {e}")
        sys.exit(255)

if __name__ == "__main__":
    main()
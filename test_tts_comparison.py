#!/usr/bin/env python3
"""
Script de comparación completa entre modelos TTS
Soporta: Azure TTS, F5-TTS, Kokoro TTS, XTTS-v2

Realiza pruebas de:
- Conectividad y salud de servicios
- Rendimiento (tiempo de síntesis)
- Calidad de audio
- Diferentes tipos de texto
- Generación de reportes comparativos

Autor: Sistema TTS Comparativo
"""

import os
import sys
import time
import json
import requests
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración básica
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Servicios TTS configurados
SERVICES = {
    'azure': {'url': 'http://localhost:5004', 'name': 'Azure TTS'},
    'f5': {'url': 'http://localhost:5005', 'name': 'F5-TTS'},
    'kokoro': {'url': 'http://localhost:5002', 'name': 'Kokoro TTS'},
    'xtts': {'url': 'http://localhost:5001', 'name': 'XTTS-v2'}
}

# Textos de prueba en español
TEST_TEXTS = {
    'corto': {
        'text': 'Hola, este es un texto corto para probar la síntesis de voz.',
        'category': 'Texto Corto',
        'expected_duration': 3.0
    },
    'medio': {
        'text': 'Este es un texto de longitud media que incluye varias oraciones para evaluar la fluidez y naturalidad de la síntesis de texto a voz en español. Contiene palabras comunes y algunas con acentos.',
        'category': 'Texto Medio',
        'expected_duration': 8.0
    },
    'largo': {
        'text': 'La síntesis de texto a voz es una tecnología fascinante que convierte texto escrito en habla audible. En español, esta tecnología debe manejar correctamente los acentos, la entonación y las particularidades fonéticas del idioma. Los modelos modernos como F5-TTS, Kokoro y XTTS-v2 utilizan técnicas avanzadas de aprendizaje profundo para generar voces naturales y expresivas.',
        'category': 'Texto Largo',
        'expected_duration': 20.0
    },
    'tecnico': {
        'text': 'La inteligencia artificial y el procesamiento de lenguaje natural han revolucionado la síntesis de voz. Los algoritmos de deep learning, redes neuronales convolucionales y transformers permiten generar audio de alta calidad.',
        'category': 'Texto Técnico',
        'expected_duration': 12.0
    },
    'numeros': {
        'text': 'El año 2024 ha sido importante para la IA. Tenemos 365 días, 24 horas, 60 minutos y 3600 segundos. Los números del 1 al 100 son fundamentales en matemáticas.',
        'category': 'Números',
        'expected_duration': 10.0
    },
    'emocional': {
        'text': '¡Qué maravilloso día! El sol brilla intensamente, los pájaros cantan alegremente y todo parece perfecto. ¿No es increíble cómo la naturaleza nos llena de felicidad?',
        'category': 'Texto Emocional',
        'expected_duration': 9.0
    }
}

# Configuración de pruebas
TEST_CONFIG = {
    'timeout': 60,  # Timeout para cada prueba
    'retries': 3,   # Número de reintentos
    'parallel_tests': True,  # Ejecutar pruebas en paralelo
    'save_audio': True,  # Guardar archivos de audio generados
    'analyze_audio': True,  # Analizar calidad de audio
    'generate_report': True,  # Generar reporte HTML
    'output_dir': f'tts_comparison_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
}

class TTSComparator:
    def __init__(self, config: Dict = None):
        self.config = config or TEST_CONFIG
        self.results = {}
        self.audio_files = {}
        self.setup_output_directory()
        
    def setup_output_directory(self):
        """Crear directorio de salida para resultados"""
        self.output_dir = Path(self.config['output_dir'])
        self.output_dir.mkdir(exist_ok=True)
        
        # Subdirectorios
        (self.output_dir / 'audio').mkdir(exist_ok=True)
        (self.output_dir / 'reports').mkdir(exist_ok=True)
        (self.output_dir / 'data').mkdir(exist_ok=True)
        
        logger.info(f"📁 Directorio de salida creado: {self.output_dir}")

    def check_service_health(self, service_key: str) -> Dict:
        """Verificar estado de salud de un servicio"""
        service = SERVICES[service_key]
        health_url = f"{service['url']}/health"
        
        try:
            start_time = time.time()
            response = requests.get(health_url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'details': response.json() if response.content else {}
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'response_time': None,
                'error': str(e)
            }

    def check_all_services_health(self) -> Dict:
        """Verificar estado de todos los servicios"""
        logger.info("🏥 Verificando estado de salud de todos los servicios...")
        
        health_results = {}
        
        for service_key in SERVICES.keys():
            logger.info(f"   Verificando {SERVICES[service_key]['name']}...")
            health_results[service_key] = self.check_service_health(service_key)
            
            status = health_results[service_key]['status']
            if status == 'healthy':
                logger.info(f"   ✅ {SERVICES[service_key]['name']}: Saludable")
            else:
                logger.warning(f"   ❌ {SERVICES[service_key]['name']}: {status}")
        
        return health_results

    def synthesize_text(self, service_key: str, text: str, voice: str = None) -> Dict:
        """Sintetizar texto con un servicio específico"""
        service = SERVICES[service_key]
        
        # Configurar endpoint y payload según el servicio
        if service_key == 'azure':
            url = f"{service['url']}/synthesize"
            payload = {
                'text': text,
                'voice': voice or 'Abril',
                'language': 'es-ES',
                'filename': f'azure_test_{int(time.time())}.mp3'
            }
        else:
            # F5, Kokoro, XTTS usan /synthesize_json
            url = f"{service['url']}/synthesize_json"
            payload = {
                'text': text,
                'language': 'es',
                'voice': voice or ('ef_dora' if service_key == 'kokoro' else 'es_female'),
                'speed': 1.0
            }
        
        try:
            start_time = time.time()
            response = requests.post(
                url, 
                json=payload, 
                headers={'Content-Type': 'application/json'},
                timeout=self.config['timeout']
            )
            synthesis_time = time.time() - start_time
            
            if response.status_code == 200:
                # Manejar respuesta según el servicio
                if service_key == 'azure':
                    # Azure devuelve el archivo de audio directamente
                    audio_data = response.content
                    result = {
                        'success': True,
                        'synthesis_time': synthesis_time,
                        'audio_data': audio_data,
                        'content_type': response.headers.get('content-type', 'audio/mp3'),
                        'audio_size': len(audio_data)
                    }
                else:
                    # Otros servicios devuelven JSON con metadata
                    try:
                        json_response = response.json()
                        result = {
                            'success': json_response.get('success', True),
                            'synthesis_time': synthesis_time,
                            'audio_duration': json_response.get('audio_duration', 0),
                            'sample_rate': json_response.get('sample_rate', 22050),
                            'model': json_response.get('model', service_key),
                            'debug_audio_file': json_response.get('debug_audio_file'),
                            'debug_audio_url': json_response.get('debug_audio_url')
                        }
                    except:
                        # Si no es JSON válido, tratar como audio directo
                        audio_data = response.content
                        result = {
                            'success': True,
                            'synthesis_time': synthesis_time,
                            'audio_data': audio_data,
                            'content_type': response.headers.get('content-type', 'audio/wav'),
                            'audio_size': len(audio_data)
                        }
                
                return result
            else:
                return {
                    'success': False,
                    'synthesis_time': synthesis_time,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'synthesis_time': None,
                'error': str(e)
            }

    def run_single_test(self, service_key: str, test_key: str) -> Dict:
        """Ejecutar una prueba individual"""
        service_name = SERVICES[service_key]['name']
        test_info = TEST_TEXTS[test_key]
        
        logger.info(f"🧪 Probando {service_name} con {test_info['category']}...")
        
        # Ejecutar síntesis
        result = self.synthesize_text(service_key, test_info['text'])
        
        # Agregar información adicional
        result.update({
            'service': service_key,
            'service_name': service_name,
            'test_type': test_key,
            'test_category': test_info['category'],
            'text_length': len(test_info['text']),
            'expected_duration': test_info['expected_duration'],
            'timestamp': datetime.now().isoformat()
        })
        
        # Guardar audio si está configurado y la síntesis fue exitosa
        if self.config['save_audio'] and result.get('success'):
            self.save_audio_file(service_key, test_key, result)
        
        return result

    def save_audio_file(self, service_key: str, test_key: str, result: Dict):
        """Guardar archivo de audio generado"""
        try:
            filename = f"{service_key}_{test_key}_{int(time.time())}"
            
            if 'audio_data' in result:
                # Servicios que devuelven audio directo (Azure)
                extension = '.mp3' if service_key == 'azure' else '.wav'
                filepath = self.output_dir / 'audio' / f"{filename}{extension}"
                with open(filepath, 'wb') as f:
                    f.write(result['audio_data'])
                    
                result['audio_file'] = str(filepath)
                logger.info(f"   💾 Audio guardado: {filepath.name}")
                
            elif result.get('debug_audio_file'):
                # Servicios con archivos de debug (F5, Kokoro, XTTS)
                debug_file = result['debug_audio_file']
                
                # Buscar archivo en directorio de debug del servicio
                possible_paths = [
                    Path(f"{service_key}/debug_audio") / debug_file,
                    Path(f"{service_key}-tts/debug_audio") / debug_file,
                    Path(f"./debug_audio") / debug_file
                ]
                
                source_path = None
                for path in possible_paths:
                    if path.exists():
                        source_path = path
                        break
                
                if source_path:
                    import shutil
                    destination = self.output_dir / 'audio' / f"{filename}.wav"
                    shutil.copy2(source_path, destination)
                    
                    result['audio_file'] = str(destination)
                    logger.info(f"   💾 Audio copiado: {destination.name}")
                else:
                    logger.warning(f"   ⚠️  Archivo de debug no encontrado: {debug_file}")
                
        except Exception as e:
            logger.warning(f"   ⚠️  Error guardando audio: {e}")

    def analyze_audio_quality(self, audio_file: str) -> Dict:
        """Analizar calidad de audio básica"""
        try:
            # Cargar audio
            audio_data, sample_rate = sf.read(audio_file)
            
            # Análisis básico
            duration = len(audio_data) / sample_rate
            rms = np.sqrt(np.mean(audio_data**2))
            peak = np.max(np.abs(audio_data))
            
            # Detectar silencios
            silence_threshold = 0.01
            silence_mask = np.abs(audio_data) < silence_threshold
            silence_ratio = np.sum(silence_mask) / len(audio_data)
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'rms_level': float(rms),
                'peak_level': float(peak),
                'silence_ratio': float(silence_ratio),
                'dynamic_range': float(peak - rms) if peak > 0 else 0,
                'file_size': os.path.getsize(audio_file)
            }
            
        except Exception as e:
            logger.warning(f"Error analizando audio {audio_file}: {e}")
            return {}

    def run_comprehensive_tests(self) -> Dict:
        """Ejecutar todas las pruebas de forma comprensiva"""
        logger.info("🚀 Iniciando pruebas comparativas completas...")
        
        # 1. Verificar estado de servicios
        health_results = self.check_all_services_health()
        
        # 2. Identificar servicios disponibles
        available_services = [
            service for service, health in health_results.items() 
            if health['status'] == 'healthy'
        ]
        
        if not available_services:
            logger.error("❌ No hay servicios disponibles para probar")
            return {'error': 'No services available'}
        
        logger.info(f"✅ Servicios disponibles: {[SERVICES[s]['name'] for s in available_services]}")
        
        # 3. Ejecutar pruebas
        all_results = []
        
        if self.config['parallel_tests']:
            # Ejecutar en paralelo
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for service_key in available_services:
                    for test_key in TEST_TEXTS.keys():
                        future = executor.submit(self.run_single_test, service_key, test_key)
                        futures.append(future)
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        logger.error(f"Error en prueba paralela: {e}")
        else:
            # Ejecutar secuencialmente
            for service_key in available_services:
                for test_key in TEST_TEXTS.keys():
                    result = self.run_single_test(service_key, test_key)
                    all_results.append(result)
        
        # 4. Analizar archivos de audio si está configurado
        if self.config['analyze_audio']:
            logger.info("🔍 Analizando calidad de audio...")
            for result in all_results:
                if result.get('success') and result.get('audio_file'):
                    audio_analysis = self.analyze_audio_quality(result['audio_file'])
                    result['audio_analysis'] = audio_analysis
        
        # 5. Compilar resultados
        compiled_results = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'health_check': health_results,
            'available_services': available_services,
            'test_results': all_results,
            'summary': self.generate_summary(all_results)
        }
        
        # 6. Guardar resultados
        self.save_results(compiled_results)
        
        # 7. Generar reportes
        if self.config['generate_report']:
            self.generate_reports(compiled_results)
        
        return compiled_results

    def generate_summary(self, results: List[Dict]) -> Dict:
        """Generar resumen de resultados"""
        summary = {
            'total_tests': len(results),
            'successful_tests': len([r for r in results if r.get('success')]),
            'failed_tests': len([r for r in results if not r.get('success')]),
            'by_service': {},
            'by_test_type': {},
            'performance_metrics': {}
        }
        
        # Agrupar por servicio
        for service_key in SERVICES.keys():
            service_results = [r for r in results if r.get('service') == service_key]
            if service_results:
                successful = [r for r in service_results if r.get('success')]
                synthesis_times = [r['synthesis_time'] for r in successful if r.get('synthesis_time')]
                
                summary['by_service'][service_key] = {
                    'name': SERVICES[service_key]['name'],
                    'total_tests': len(service_results),
                    'successful': len(successful),
                    'success_rate': len(successful) / len(service_results) * 100,
                    'avg_synthesis_time': np.mean(synthesis_times) if synthesis_times else None,
                    'min_synthesis_time': np.min(synthesis_times) if synthesis_times else None,
                    'max_synthesis_time': np.max(synthesis_times) if synthesis_times else None
                }
        
        # Agrupar por tipo de prueba
        for test_key in TEST_TEXTS.keys():
            test_results = [r for r in results if r.get('test_type') == test_key]
            if test_results:
                successful = [r for r in test_results if r.get('success')]
                
                summary['by_test_type'][test_key] = {
                    'category': TEST_TEXTS[test_key]['category'],
                    'total_tests': len(test_results),
                    'successful': len(successful),
                    'success_rate': len(successful) / len(test_results) * 100
                }
        
        return summary

    def save_results(self, results: Dict):
        """Guardar resultados en archivo JSON"""
        results_file = self.output_dir / 'data' / 'results.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Resultados guardados: {results_file}")

    def generate_reports(self, results: Dict):
        """Generar reportes visuales y HTML"""
        logger.info("📊 Generando reportes...")
        
        # Generar gráficos
        self.generate_performance_charts(results)
        
        # Generar reporte HTML
        self.generate_html_report(results)
        
        logger.info(f"📈 Reportes generados en: {self.output_dir / 'reports'}")

    def generate_performance_charts(self, results: Dict):
        """Generar gráficos de rendimiento"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Configurar estilo
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Datos para gráficos
            test_results = results['test_results']
            successful_results = [r for r in test_results if r.get('success') and r.get('synthesis_time')]
            
            if not successful_results:
                logger.warning("No hay resultados exitosos para generar gráficos")
                return
            
            # Gráfico 1: Tiempo de síntesis por servicio
            plt.figure(figsize=(12, 8))
            
            services = list(set(r['service'] for r in successful_results))
            service_names = [SERVICES[s]['name'] for s in services]
            
            synthesis_times = []
            for service in services:
                times = [r['synthesis_time'] for r in successful_results if r['service'] == service]
                synthesis_times.append(times)
            
            plt.subplot(2, 2, 1)
            box_plot = plt.boxplot(synthesis_times, labels=service_names)
            plt.title('Tiempo de Síntesis por Servicio')
            plt.ylabel('Tiempo (segundos)')
            plt.xticks(rotation=45)
            
            # Gráfico 2: Tiempo por tipo de texto
            plt.subplot(2, 2, 2)
            test_types = list(set(r['test_type'] for r in successful_results))
            test_categories = [TEST_TEXTS[t]['category'] for t in test_types]
            
            type_times = []
            for test_type in test_types:
                times = [r['synthesis_time'] for r in successful_results if r['test_type'] == test_type]
                type_times.append(times)
            
            plt.boxplot(type_times, labels=test_categories)
            plt.title('Tiempo por Tipo de Texto')
            plt.ylabel('Tiempo (segundos)')
            plt.xticks(rotation=45)
            
            # Gráfico 3: Tasa de éxito por servicio
            plt.subplot(2, 2, 3)
            success_rates = []
            for service in services:
                service_results = [r for r in test_results if r['service'] == service]
                success_rate = len([r for r in service_results if r.get('success')]) / len(service_results) * 100
                success_rates.append(success_rate)
            
            bars = plt.bar(service_names, success_rates)
            plt.title('Tasa de Éxito por Servicio')
            plt.ylabel('Porcentaje (%)')
            plt.ylim(0, 100)
            plt.xticks(rotation=45)
            
            # Añadir valores a las barras
            for bar, rate in zip(bars, success_rates):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{rate:.1f}%', ha='center', va='bottom')
            
            # Gráfico 4: Tamaño de texto vs tiempo
            plt.subplot(2, 2, 4)
            text_lengths = [r['text_length'] for r in successful_results]
            times = [r['synthesis_time'] for r in successful_results]
            services_for_scatter = [r['service'] for r in successful_results]
            
            # Scatter plot coloreado por servicio
            colors = plt.cm.tab10(np.linspace(0, 1, len(set(services_for_scatter))))
            color_map = {service: colors[i] for i, service in enumerate(set(services_for_scatter))}
            
            for service in set(services_for_scatter):
                service_lengths = [length for length, s in zip(text_lengths, services_for_scatter) if s == service]
                service_times = [time for time, s in zip(times, services_for_scatter) if s == service]
                plt.scatter(service_lengths, service_times, 
                           label=SERVICES[service]['name'], 
                           color=color_map[service], alpha=0.7)
            
            plt.xlabel('Longitud del Texto (caracteres)')
            plt.ylabel('Tiempo de Síntesis (segundos)')
            plt.title('Longitud vs Tiempo de Síntesis')
            plt.legend()
            
            plt.tight_layout()
            
            # Guardar gráfico
            chart_file = self.output_dir / 'reports' / 'performance_charts.png'
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Gráficos guardados: {chart_file}")
            
        except Exception as e:
            logger.error(f"Error generando gráficos: {e}")

    def generate_html_report(self, results: Dict):
        """Generar reporte HTML completo"""
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Comparativo TTS</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #ecf0f1; padding: 15px; border-radius: 8px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #2c3e50; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .services-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .service-card {{ border: 1px solid #bdc3c7; border-radius: 8px; padding: 15px; }}
        .service-card h3 {{ margin: 0 0 15px 0; color: #2c3e50; }}
        .metric {{ display: flex; justify-content: space-between; margin: 5px 0; padding: 5px; background: #f8f9fa; border-radius: 4px; }}
        .success {{ color: #27ae60; }}
        .error {{ color: #e74c3c; }}
        .warning {{ color: #f39c12; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #bdc3c7; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .chart-container {{ text-align: center; margin: 20px 0; }}
        .timestamp {{ text-align: center; color: #7f8c8d; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Reporte Comparativo de Modelos TTS</h1>
        <p class="timestamp">Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        
        <h2>📊 Resumen General</h2>
        <div class="summary">
            <div class="summary-card">
                <h3>Total de Pruebas</h3>
                <div class="value">{results['summary']['total_tests']}</div>
            </div>
            <div class="summary-card">
                <h3>Pruebas Exitosas</h3>
                <div class="value success">{results['summary']['successful_tests']}</div>
            </div>
            <div class="summary-card">
                <h3>Pruebas Fallidas</h3>
                <div class="value error">{results['summary']['failed_tests']}</div>
            </div>
            <div class="summary-card">
                <h3>Servicios Disponibles</h3>
                <div class="value">{len(results['available_services'])}</div>
            </div>
        </div>
        
        <h2>🏥 Estado de Servicios</h2>
        <div class="services-grid">
        """
        
        # Estado de servicios
        for service_key, health in results['health_check'].items():
            service_name = SERVICES[service_key]['name']
            status_class = 'success' if health['status'] == 'healthy' else 'error'
            response_time = f"{health['response_time']:.3f}s" if health['response_time'] else 'N/A'
            
            html_content += f"""
            <div class="service-card">
                <h3>{service_name}</h3>
                <div class="metric">
                    <span>Estado:</span>
                    <span class="{status_class}">{health['status'].upper()}</span>
                </div>
                <div class="metric">
                    <span>Tiempo de Respuesta:</span>
                    <span>{response_time}</span>
                </div>
                {f'<div class="metric"><span>Error:</span><span class="error">{health["error"]}</span></div>' if health.get('error') else ''}
            </div>
            """
        
        html_content += """
        </div>
        
        <h2>🎯 Rendimiento por Servicio</h2>
        <div class="services-grid">
        """
        
        # Rendimiento por servicio
        for service_key, service_summary in results['summary']['by_service'].items():
            # Manejar valores None de manera segura
            avg_time = f"{service_summary['avg_synthesis_time']:.3f}s" if service_summary['avg_synthesis_time'] is not None else 'N/A'
            min_time = f"{service_summary['min_synthesis_time']:.3f}s" if service_summary['min_synthesis_time'] is not None else 'N/A'
            max_time = f"{service_summary['max_synthesis_time']:.3f}s" if service_summary['max_synthesis_time'] is not None else 'N/A'
            
            html_content += f"""
            <div class="service-card">
                <h3>{service_summary['name']}</h3>
                <div class="metric">
                    <span>Tasa de Éxito:</span>
                    <span class="success">{service_summary['success_rate']:.1f}%</span>
                </div>
                <div class="metric">
                    <span>Tiempo Promedio:</span>
                    <span>{avg_time}</span>
                </div>
                <div class="metric">
                    <span>Tiempo Mínimo:</span>
                    <span>{min_time}</span>
                </div>
                <div class="metric">
                    <span>Tiempo Máximo:</span>
                    <span>{max_time}</span>
                </div>
            </div>
            """
        
        html_content += """
        </div>
        
        <h2>📈 Gráficos de Rendimiento</h2>
        <div class="chart-container">
            <img src="performance_charts.png" alt="Gráficos de Rendimiento" style="max-width: 100%; height: auto;">
        </div>
        
        <h2>📋 Resultados Detallados</h2>
        <table>
            <thead>
                <tr>
                    <th>Servicio</th>
                    <th>Tipo de Prueba</th>
                    <th>Estado</th>
                    <th>Tiempo (s)</th>
                    <th>Longitud Texto</th>
                    <th>Duración Audio</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Tabla de resultados detallados
        for result in results['test_results']:
            status_class = 'success' if result.get('success') else 'error'
            status_text = '✅ Éxito' if result.get('success') else '❌ Fallo'
            synthesis_time = f"{result['synthesis_time']:.3f}" if result.get('synthesis_time') else 'N/A'
            audio_duration = f"{result.get('audio_duration', 0):.2f}s" if result.get('audio_duration') else 'N/A'
            
            html_content += f"""
                <tr>
                    <td>{result.get('service_name', 'N/A')}</td>
                    <td>{result.get('test_category', 'N/A')}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{synthesis_time}</td>
                    <td>{result.get('text_length', 0)}</td>
                    <td>{audio_duration}</td>
                </tr>
            """
        
        html_content += """
            </tbody>
        </table>
        
        <h2>🔧 Configuración de Pruebas</h2>
        <table>
            <tr><th>Parámetro</th><th>Valor</th></tr>
        """
        
        # Configuración
        for key, value in self.config.items():
            html_content += f"<tr><td>{key}</td><td>{value}</td></tr>"
        
        html_content += """
        </table>
        
        <div class="timestamp">
            <p>Reporte generado automáticamente por el Sistema de Comparación TTS</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Guardar reporte HTML
        report_file = self.output_dir / 'reports' / 'tts_comparison_report.html'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"📄 Reporte HTML generado: {report_file}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Comparador de Servicios TTS')
    parser.add_argument('--services', nargs='+', 
                       choices=['azure', 'f5', 'kokoro', 'xtts', 'all'],
                       default=['all'], 
                       help='Servicios a probar')
    parser.add_argument('--tests', nargs='+',
                       choices=['corto', 'medio', 'largo', 'tecnico', 'numeros', 'emocional', 'all'],
                       default=['all'],
                       help='Tipos de prueba a ejecutar')
    parser.add_argument('--output', '-o', 
                       help='Directorio de salida')
    parser.add_argument('--no-parallel', action='store_true',
                       help='Ejecutar pruebas secuencialmente')
    parser.add_argument('--no-audio', action='store_true',
                       help='No guardar archivos de audio')
    parser.add_argument('--no-report', action='store_true',
                       help='No generar reportes HTML')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Salida detallada')
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configurar pruebas
    config = TEST_CONFIG.copy()
    
    if args.output:
        config['output_dir'] = args.output
    if args.no_parallel:
        config['parallel_tests'] = False
    if args.no_audio:
        config['save_audio'] = False
    if args.no_report:
        config['generate_report'] = False
    
    # Declarar variables globales al inicio
    global SERVICES, TEST_TEXTS
    
    # Filtrar servicios si no es 'all'
    if 'all' not in args.services:
        SERVICES = {k: v for k, v in SERVICES.items() if k in args.services}
    
    # Filtrar pruebas si no es 'all'
    if 'all' not in args.tests:
        TEST_TEXTS = {k: v for k, v in TEST_TEXTS.items() if k in args.tests}
    
    # Ejecutar comparador
    comparator = TTSComparator(config)
    
    print("🎤 Comparador de Servicios TTS - Inicializando...")
    logger.info("🎯 Iniciando comparación de servicios TTS...")
    logger.info(f"🔧 Servicios a probar: {list(SERVICES.keys())}")
    logger.info(f"📝 Tipos de prueba: {list(TEST_TEXTS.keys())}")
    
    try:
        results = comparator.run_comprehensive_tests()
        
        if 'error' in results:
            logger.error(f"❌ Error en las pruebas: {results['error']}")
            return 1
        
        logger.info("✅ Pruebas completadas exitosamente")
        logger.info(f"📊 Resultados disponibles en: {comparator.output_dir}")
        
        # Mostrar resumen
        summary = results['summary']
        logger.info(f"📈 Resumen: {summary['successful_tests']}/{summary['total_tests']} pruebas exitosas")
        
        print("\n🎯 RESUMEN DE RESULTADOS:")
        print(f"Total de pruebas: {summary['total_tests']}")
        print(f"Exitosas: {summary['successful_tests']}")
        print(f"Fallidas: {summary['failed_tests']}")
        print("\n📊 Por servicio:")
        
        for service_key, service_summary in summary['by_service'].items():
            service_name = service_summary['name']
            success_rate = service_summary['success_rate']
            avg_time = service_summary.get('avg_synthesis_time')
            
            print(f"  {service_name}:")
            print(f"    Tasa de éxito: {success_rate:.1f}%")
            if avg_time is not None:
                print(f"    Tiempo promedio: {avg_time:.3f}s")
            
            logger.info(f"   {service_name}: {success_rate:.1f}% éxito")
        
        print(f"\n📁 Resultados completos en: {comparator.output_dir}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("❌ Pruebas interrumpidas por el usuario")
        return 1
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
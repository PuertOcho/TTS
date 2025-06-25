#!/bin/bash

# Script de demostración rápida del sistema de comparación TTS
# Ejecuta pruebas básicas para mostrar las capacidades

echo "🎤 DEMO: Sistema de Comparación TTS"
echo "=================================="
echo ""

# Verificar servicios disponibles
echo "🔍 Verificando servicios disponibles..."
available_count=0

services=("azure:5004" "f5:5005" "kokoro:5002" "xtts:5001")
for service in "${services[@]}"; do
    name="${service%:*}"
    port="${service#*:}"
    
    if curl -s -f "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo "  ✅ ${name^} TTS: Disponible"
        ((available_count++))
    else
        echo "  ❌ ${name^} TTS: No disponible"
    fi
done

if [ $available_count -eq 0 ]; then
    echo ""
    echo "❌ No hay servicios disponibles para la demo."
    echo "   Inicia al menos un servicio con:"
    echo "   cd [servicio] && docker-compose up -d"
    exit 1
fi

echo ""
echo "✅ $available_count servicios disponibles para la demo"
echo ""

# Ejecutar demo con pruebas básicas
echo "🚀 Ejecutando demo con pruebas básicas..."
echo "   - Solo textos corto y medio"
echo "   - Guardado de audio activado"
echo "   - Generación de reportes activada"
echo ""

# Crear directorio de demo
demo_dir="demo_results_$(date +%Y%m%d_%H%M%S)"

# Ejecutar comparación de demo
python3 test_tts_comparison.py \
    --tests corto medio \
    --output "$demo_dir" \
    --verbose

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ Demo completada exitosamente!"
    echo ""
    echo "📁 Resultados en: $demo_dir"
    
    # Mostrar contenido generado
    if [ -d "$demo_dir" ]; then
        echo ""
        echo "📊 Archivos generados:"
        echo "   Audios: $(ls $demo_dir/audio/ 2>/dev/null | wc -l) archivos"
        echo "   Datos: $(ls $demo_dir/data/ 2>/dev/null | wc -l) archivos"
        echo "   Reportes: $(ls $demo_dir/reports/ 2>/dev/null | wc -l) archivos"
        
        # Intentar abrir reporte si existe
        report_file="$demo_dir/reports/tts_comparison_report.html"
        if [ -f "$report_file" ]; then
            echo ""
            echo "🌐 Abriendo reporte en el navegador..."
            
            if command -v xdg-open &> /dev/null; then
                xdg-open "$report_file" 2>/dev/null &
            elif command -v open &> /dev/null; then
                open "$report_file" 2>/dev/null &
            else
                echo "   Abre manualmente: file://$(pwd)/$report_file"
            fi
        fi
    fi
    
    echo ""
    echo "🎯 Para pruebas completas usa:"
    echo "   ./run_tts_comparison.sh"
    echo ""
    echo "🔧 Para opciones avanzadas:"
    echo "   ./run_tts_comparison.sh -h"
else
    echo "❌ Error en la demo (código: $exit_code)"
    echo "   Verifica que los servicios estén ejecutándose"
    echo "   Revisa los logs para más detalles"
fi

echo ""
echo "�� Demo finalizada" 
#!/bin/bash

# Script para ejecutar comparación de servicios TTS
# Autor: Sistema TTS Comparativo

echo "🎤 Comparador de Servicios TTS - Script de Ejecución"
echo "=================================================="

# Verificar si Python está disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 no encontrado"
    exit 1
fi

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  -s, --services SERVICES   Servicios a probar (azure,f5,kokoro,xtts,all)"
    echo "  -t, --tests TESTS         Tipos de prueba (corto,medio,largo,tecnico,numeros,emocional,all)"
    echo "  -o, --output DIR          Directorio de salida"
    echo "  --no-parallel            Ejecutar pruebas secuencialmente"
    echo "  --no-audio               No guardar archivos de audio"
    echo "  --no-report              No generar reportes HTML"
    echo "  -v, --verbose            Salida detallada"
    echo "  -h, --help               Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0                                    # Probar todos los servicios"
    echo "  $0 -s azure f5                       # Solo Azure y F5-TTS"
    echo "  $0 -t corto medio                    # Solo textos cortos y medios"
    echo "  $0 -o ./mis_resultados               # Directorio personalizado"
    echo "  $0 --no-parallel -v                 # Secuencial con salida detallada"
    echo ""
}

# Función para verificar servicios
check_services() {
    echo "🏥 Verificando servicios TTS..."
    
    services=("azure:5004" "f5:5005" "kokoro:5002" "xtts:5001")
    available_services=()
    
    for service in "${services[@]}"; do
        name="${service%:*}"
        port="${service#*:}"
        
        if curl -s -f "http://localhost:${port}/health" > /dev/null 2>&1; then
            echo "  ✅ ${name^} TTS (puerto ${port}): Disponible"
            available_services+=("$name")
        else
            echo "  ❌ ${name^} TTS (puerto ${port}): No disponible"
        fi
    done
    
    if [ ${#available_services[@]} -eq 0 ]; then
        echo ""
        echo "❌ No hay servicios TTS disponibles."
        echo "   Asegúrate de que los servicios estén ejecutándose:"
        echo "   - cd azure-tts && docker-compose up -d"
        echo "   - cd f5-tts && docker-compose up -d"
        echo "   - cd kokoro && docker-compose up -d"
        echo "   - cd xtts-v2 && docker-compose up -d"
        exit 1
    fi
    
    echo ""
    echo "✅ Servicios disponibles: ${available_services[*]}"
    echo ""
}

# Función para instalar dependencias
install_dependencies() {
    echo "📦 Verificando dependencias Python..."
    
    if [ ! -f "requirements_comparison.txt" ]; then
        echo "   Creando archivo de requisitos..."
        cat > requirements_comparison.txt << EOF
requests>=2.28.0
numpy>=1.21.0
soundfile>=0.10.0
matplotlib>=3.5.0
seaborn>=0.11.0
pandas>=1.3.0
pathlib
EOF
    fi
    
    if ! python3 -c "import requests, numpy, soundfile, matplotlib, seaborn, pandas" 2>/dev/null; then
        echo "   Instalando dependencias faltantes..."
        python3 -m pip install -r requirements_comparison.txt
        
        if [ $? -ne 0 ]; then
            echo "❌ Error instalando dependencias"
            exit 1
        fi
    fi
    
    echo "   ✅ Dependencias verificadas"
    echo ""
}

# Función para ejecutar pruebas
run_tests() {
    echo "🚀 Ejecutando pruebas comparativas..."
    echo ""
    
    # Construir comando
    cmd="python3 test_tts_comparison.py"
    
    # Agregar argumentos
    if [ ! -z "$SERVICES" ]; then
        cmd="$cmd --services $SERVICES"
    fi
    
    if [ ! -z "$TESTS" ]; then
        cmd="$cmd --tests $TESTS"
    fi
    
    if [ ! -z "$OUTPUT" ]; then
        cmd="$cmd --output $OUTPUT"
    fi
    
    if [ "$NO_PARALLEL" = true ]; then
        cmd="$cmd --no-parallel"
    fi
    
    if [ "$NO_AUDIO" = true ]; then
        cmd="$cmd --no-audio"
    fi
    
    if [ "$NO_REPORT" = true ]; then
        cmd="$cmd --no-report"
    fi
    
    if [ "$VERBOSE" = true ]; then
        cmd="$cmd --verbose"
    fi
    
    echo "Comando: $cmd"
    echo ""
    
    # Ejecutar
    eval $cmd
    return_code=$?
    
    echo ""
    if [ $return_code -eq 0 ]; then
        echo "✅ Pruebas completadas exitosamente"
    else
        echo "❌ Error en las pruebas (código: $return_code)"
    fi
    
    return $return_code
}

# Función para abrir resultados
open_results() {
    if [ $return_code -eq 0 ] && [ -z "$NO_REPORT" ]; then
        # Buscar el directorio de resultados más reciente
        result_dir=$(ls -dt tts_comparison_results_* 2>/dev/null | head -1)
        
        if [ ! -z "$result_dir" ] && [ -d "$result_dir" ]; then
            report_file="$result_dir/reports/tts_comparison_report.html"
            
            if [ -f "$report_file" ]; then
                echo ""
                echo "📊 Reporte generado: $report_file"
                
                # Intentar abrir el reporte en el navegador
                if command -v xdg-open &> /dev/null; then
                    echo "   Abriendo reporte en el navegador..."
                    xdg-open "$report_file" 2>/dev/null &
                elif command -v open &> /dev/null; then
                    echo "   Abriendo reporte en el navegador..."
                    open "$report_file" 2>/dev/null &
                else
                    echo "   Abre manualmente: file://$(pwd)/$report_file"
                fi
            fi
            
            echo "📁 Resultados completos en: $result_dir"
        fi
    fi
}

# Inicializar variables
SERVICES=""
TESTS=""
OUTPUT=""
NO_PARALLEL=false
NO_AUDIO=false
NO_REPORT=false
VERBOSE=false

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--services)
            shift
            while [[ $# -gt 0 ]] && [[ ! $1 =~ ^- ]]; do
                SERVICES="$SERVICES $1"
                shift
            done
            ;;
        -t|--tests)
            shift
            while [[ $# -gt 0 ]] && [[ ! $1 =~ ^- ]]; do
                TESTS="$TESTS $1"
                shift
            done
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        --no-parallel)
            NO_PARALLEL=true
            shift
            ;;
        --no-audio)
            NO_AUDIO=true
            shift
            ;;
        --no-report)
            NO_REPORT=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "❌ Opción desconocida: $1"
            echo "Usa -h o --help para ver las opciones disponibles"
            exit 1
            ;;
    esac
done

# Verificar que el script Python existe
if [ ! -f "test_tts_comparison.py" ]; then
    echo "❌ Error: test_tts_comparison.py no encontrado"
    echo "   Asegúrate de ejecutar este script desde el directorio correcto"
    exit 1
fi

# Ejecutar verificaciones y pruebas
check_services
install_dependencies
run_tests
return_code=$?
open_results

echo ""
echo "🏁 Proceso completado"
exit $return_code 
#!/bin/bash

echo "🎤 SCRIPT DE COMPARACIÓN COMPLETA DE MODELOS TTS CON AUDIO"
echo "=========================================================="
echo ""

# Verificar que estamos en el directorio correcto
if [[ ! -d "azure-tts-ms" || ! -d "f5-tts-ms" || ! -d "kokoro-tts-ms" || ! -d "xtts-v2-tts-ms" ]]; then
    echo "❌ Error: No se encontraron los directorios de los modelos TTS"
    echo "   Asegúrate de ejecutar este script desde el directorio raíz del proyecto TTSms"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 no está instalado"
    exit 1
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "❌ Error: Docker Compose no está disponible"
    exit 1
fi

echo "✅ Verificaciones del sistema completadas"
echo ""

# Instalar dependencias si es necesario
echo "📦 Instalando dependencias Python..."
python3 -m pip install -r requirements_comparison.txt --quiet

echo "✅ Dependencias instaladas"
echo ""

# Verificar que no hay servicios corriendo
echo "🔍 Verificando servicios existentes..."
for port in 5001 5002 5004 5005; do
    if lsof -i:$port &> /dev/null; then
        echo "⚠️ Advertencia: Puerto $port está en uso. Deteniendo servicios..."
        # Intentar detener servicios en cada directorio
        for dir in azure-tts-ms f5-tts-ms kokoro-tts-ms xtts-v2-tts-ms; do
            if [[ -d "$dir" ]]; then
                (cd "$dir" && docker compose down &> /dev/null)
            fi
        done
        sleep 5
        break
    fi
done

echo "✅ Puertos libres"
echo ""

# Ejecutar el script de comparación con audio
echo "🚀 INICIANDO COMPARACIÓN AUTOMÁTICA CON CAPTURA DE AUDIO..."
echo "   Este proceso puede tardar 30-60 minutos dependiendo de tu hardware"
echo "   Los servicios se levantarán y apagarán automáticamente"
echo "   🎵 ¡Ahora se capturarán muestras de audio de cada modelo!"
echo ""
echo "   Presiona Ctrl+C para cancelar en cualquier momento"
echo ""

sleep 3

python3 generate_tts_comparison_report.py

exit_code=$?

if [[ $exit_code -eq 0 ]]; then
    echo ""
    echo "🎉 ¡COMPARACIÓN CON AUDIO COMPLETADA EXITOSAMENTE!"
    echo ""
    echo "📁 Los reportes se han guardado en: tts_comparison_reports/"
    echo "🎵 Los archivos de audio están en: tts_comparison_reports/audio/"
    echo ""
    echo "📄 Archivos generados:"
    ls -la tts_comparison_reports/ | tail -5
    echo ""
    echo "🔗 Para ver el reporte HTML CON REPRODUCTORES DE AUDIO, abre el archivo .html en tu navegador"
    echo "🎵 ¡Ahora puedes escuchar las muestras de audio directamente en el reporte!"
else
    echo ""
    echo "❌ La comparación con audio falló con código de salida: $exit_code"
    echo "   Revisa los logs arriba para más detalles"
fi

exit $exit_code

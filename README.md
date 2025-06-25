# 🎤 Comparador de Modelos TTS (Text-to-Speech) con Métricas y Audio

## Descripción

Este proyecto permite comparar de forma **automatizada y visual** distintos modelos de síntesis de voz (TTS) auto-hospedados y en la nube, midiendo rendimiento, consumo de recursos y calidad de audio. Genera un **reporte HTML profesional** con reproductores de audio para comparar la naturalidad y velocidad de cada modelo.

### Modelos soportados:
- **Azure TTS** (Microsoft, cloud)
- **F5-TTS** (Spanish-F5, HuggingFace)
- **Kokoro TTS** (ONNX, multilingüe)
- **XTTS-v2** (Coqui, clonación de voz)

---

## 🚀 Estructura del Proyecto

```
TTSms/
├── azure-tts-ms/
├── f5-tts-ms/
├── kokoro-tts-ms/
├── xtts-v2-tts-ms/
├── tts_comparison_reports/
│   ├── tts_comparison_report_with_audio_YYYYMMDD_HHMMSS.html
│   ├── tts_comparison_data_with_audio_YYYYMMDD_HHMMSS.json
│   └── audio/
│       ├── 01_azure_tts_synthesis_basic.wav
│       └── ...
├── run_tts_comparison_with_audio.sh
├── requirements_comparison.txt
└── README.md
```

---

## 📦 Dependencias

- **Python 3.7+**
- **Docker** y **Docker Compose**
- **NVIDIA GPU** (recomendado, pero funciona en CPU)
- Paquetes Python: `requests`, `psutil`, `statistics`, `jq` (para análisis opcional)

Instalación rápida de dependencias:
```bash
pip install -r requirements_comparison.txt
```

---

## 🛠️ Uso Rápido

### 1. Verifica el sistema (opcional)
```bash
python3 test_comparison_setup.py
```

### 2. Ejecuta la comparación completa con audio
```bash
./run_tts_comparison_with_audio.sh
```

- El script levantará y apagará cada modelo secuencialmente
- Monitoreará recursos (CPU, RAM, GPU)
- Capturará muestras de audio
- Generará un reporte HTML con reproductores
- Abrirá el reporte automáticamente en tu navegador

---

## 📄 ¿Qué incluye el reporte?

- **Resumen ejecutivo** con ranking de modelos
- **Métricas de rendimiento**: tiempo de respuesta, uso de CPU/GPU/RAM
- **Reproductores de audio** para cada modelo y texto de prueba
- **Comparación visual y auditiva**
- **Recomendaciones de uso** según caso
- **Datos JSON** para análisis avanzado

### Ejemplo de sección de audio:
```
🎵 Muestras de Audio por Modelo
├── Azure TTS
│   ├── 🎵 Prueba básica: [▶️ Reproductor]
│   └── 🎵 Texto largo: [▶️ Reproductor]
├── F5-TTS
│   └── ...
```

---

## 📊 Métricas que se comparan
- ⏱️ **Tiempo de respuesta** (por texto)
- 💻 **CPU promedio y pico**
- 🧠 **RAM promedio y pico**
- 🎮 **GPU y VRAM** utilizadas
- 🎵 **Calidad y naturalidad de audio** (subjetivo, vía reproductor)

---

## 🏆 Ejemplo de Ranking (puede variar según hardware)
| Modelo      | Tiempo | CPU   | GPU  | Audios |
|-------------|--------|-------|------|--------|
| Kokoro TTS  | 0.54s  | 57.8% | 12%  |   2    |
| XTTS-v2     | 2.12s  | 17.6% | 82%  |   2    |
| Azure TTS   | 6.65s  | 14.7% | 12%  |   2    |
| F5-TTS      | 8.28s  | 22.8% | 98%  |   2    |

---

## 🎯 Recomendaciones de uso
- **Azure TTS**: Producción comercial, múltiples idiomas
- **Kokoro TTS**: Máxima velocidad, auto-hospedado
- **XTTS-v2**: Clonación de voz, control total
- **F5-TTS**: Español nativo, acento perfecto

---

## 🛡️ Solución de problemas
- Si un modelo se cuelga, el sistema lo salta y sigue con el resto
- Si no tienes GPU, la comparación será más lenta
- Si algún puerto está ocupado, el script intentará liberar recursos automáticamente

---

## 📬 Contacto y soporte

¿Dudas, bugs o sugerencias? Abre un issue o contacta al responsable del proyecto.

---

**¡Disfruta comparando y escuchando la diferencia entre los mejores modelos TTS!** 🎵🚀 
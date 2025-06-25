# 🎤 Comparador de Modelos TTS (Text-to-Speech)

## Descripción

Este proyecto permite comparar de forma **automatizada y visual** distintos modelos de síntesis de voz (TTS) auto-hospedados y en la nube, midiendo rendimiento, consumo de recursos y calidad de audio. Genera un **reporte HTML profesional** con reproductores de audio para comparar la naturalidad y velocidad de cada modelo.

### Modelos soportados:
- **Azure TTS** (Microsoft, cloud)
- **F5-TTS** (Spanish-F5, HuggingFace)
- **Kokoro TTS** (ONNX, multilingüe)
- **XTTS-v2** (Coqui, clonación de voz)

---

## 📊 Comparativa visual, Tiempo de Respuesta por Modelo

![Comparativa Tiempos TTS](https://quickchart.io/chart?c=%7B%22type%22%3A%22bar%22%2C%22data%22%3A%7B%22labels%22%3A%5B%22F5-TTS%22%2C%22Azure%20TTS%22%2C%22XTTS-v2%22%2C%22Kokoro%20TTS%22%5D%2C%22datasets%22%3A%5B%7B%22label%22%3A%22Tiempo%20de%20respuesta%20(s)%22%2C%22data%22%3A%5B8.3%2C6.6%2C2.1%2C0.5%5D%2C%22backgroundColor%22%3A%5B%22%233498db%22%2C%22%23e67e22%22%2C%22%232ecc71%22%2C%22%239b59b6%22%5D%7D%5D%7D%2C%22options%22%3A%7B%22scales%22%3A%7B%22yAxes%22%3A%5B%7B%22ticks%22%3A%7B%22beginAtZero%22%3Atrue%7D%7D%5D%7D%7D%7D)

> **Interpretación:**
> - **Kokoro TTS** es el más rápido (~0.5s), seguido de **XTTS-v2** (~2s), **Azure TTS** (~6.6s) y **F5-TTS** (~8.3s).

### 💻 Tabla de Recursos (Ejemplo)

| Modelo      | CPU (%) | GPU (%) | RAM (GB) | Tiempo (s) |
|-------------|---------|---------|----------|------------|
| Kokoro TTS  | 57.8    | 12      | 1.2      | 0.54       |
| XTTS-v2     | 17.6    | 82      | 2.1      | 2.12       |
| Azure TTS   | 14.7    | 12      | 1.0      | 6.65       |
| F5-TTS      | 22.8    | 98      | 2.5      | 8.28       |

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


**¡Disfruta comparando y escuchando la diferencia entre los mejores modelos TTS!** 🎵🚀 
# Comparación de APIs de Traducción - Costes 2026

## Resumen Ejecutivo

Actualmente estás usando **Gemini 1.5 Flash** que es relativamente económico, pero hay alternativas aún más baratas dependiendo de tus necesidades.

## Comparación de Precios (por millón de caracteres)

### 1. **Microsoft Azure Translator** - MÁS BARATO
- **Precio**: $10 USD por millón de caracteres
- **Tier gratuito**: No especificado
- **Ventajas**: 
  - Precio más bajo del mercado
  - Buena calidad para traducciones técnicas
  - Soporte para 100+ idiomas
- **Desventajas**: 
  - Requiere cuenta Azure
  - Configuración más compleja

### 2. **Amazon Translate**
- **Precio**: $15 USD por millón de caracteres
- **Tier gratuito**: 2 millones de caracteres/mes durante 12 meses
- **Ventajas**:
  - Tier gratuito generoso
  - Integración con AWS
  - Buena calidad
- **Desventajas**:
  - Requiere cuenta AWS

### 3. **Google Cloud Translation API**
- **Precio**: $20 USD por millón de caracteres
- **Tier gratuito**: 500,000 caracteres/mes
- **Ventajas**:
  - Misma infraestructura que usas ahora
  - Fácil migración desde Gemini
  - Tier gratuito permanente
- **Desventajas**:
  - Más caro que Azure/Amazon

### 4. **DeepL API**
- **Precio**: $25 USD por millón de caracteres + $5.49/mes
- **Tier gratuito**: 500,000 caracteres/mes
- **Ventajas**:
  - MEJOR CALIDAD para idiomas europeos (especialmente EN→NL)
  - Tier gratuito generoso
  - Especializado en calidad, no cantidad
- **Desventajas**:
  - Más caro
  - Cuota mensual adicional

### 5. **Gemini 1.5 Flash** (ACTUAL)
- **Precio**: ~$0.50 input + $3.00 output por millón de tokens
- **Tier gratuito**: Sí (límites variables)
- **Ventajas**:
  - Ya configurado
  - Flexible (puedes ajustar prompts)
  - Tier gratuito disponible
- **Desventajas**:
  - Precio basado en tokens (menos predecible)
  - Puede ser más caro para textos largos

## Recomendaciones

### Para TU caso específico (EN → NL, textos técnicos):

1. **MEJOR OPCIÓN: DeepL API Free Tier**
   - Razón: 500k caracteres gratis/mes + MEJOR calidad para holandés
   - Implementación: Relativamente fácil
   - Coste: $0 hasta 500k caracteres

2. **OPCIÓN MÁS BARATA (si superas free tier): Azure Translator**
   - Razón: $10/millón es el más barato
   - Implementación: Moderada complejidad
   - Coste: Mínimo

3. **OPCIÓN ACTUAL (Gemini 1.5 Flash)**
   - Mantener si:
     - Estás en tier gratuito
     - Necesitas flexibilidad en prompts
     - Volumen bajo (<100k caracteres/mes)

## Cálculo de Costes para tu Volumen

Asumiendo 1 millón de caracteres/mes:
- **Azure**: $10/mes
- **Amazon**: GRATIS (primer año), luego $15/mes
- **Google Translate**: $20/mes
- **DeepL**: $30.49/mes ($25 + $5.49)
- **Gemini**: Variable (~$15-25/mes estimado)

## Próximos Pasos Recomendados

1. **Probar DeepL Free Tier primero**
   - 500k caracteres gratis
   - Mejor calidad para NL
   - Fácil de integrar

2. **Si necesitas más volumen → Azure**
   - Más barato a largo plazo
   - Buena calidad

3. **Mantener Gemini como backup**
   - Para casos especiales
   - Cuando necesites ajustar la traducción con prompts

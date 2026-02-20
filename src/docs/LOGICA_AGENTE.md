# Protocolo de Decisiones Técnicas: Sistema Performance Guard NSCA

Este documento describe la arquitectura lógica y los criterios de evaluación empleados por el agente de inteligencia artificial para la integración de datos biométricos y directrices de seguridad deportiva.

## 1. Gestión de Periodos de Transición
El sistema identifica automáticamente fases de retorno al entrenamiento tras periodos de inactividad iguales o superiores a dos semanas.

### Fundamento Científico
Según las directrices de consenso de la CSCCa y la NSCA, aproximadamente el 60% de las lesiones no traumáticas en entornos competitivos ocurren durante estas fases de transición.

### Implementación de la Regla 50/30/20/10
Ante la detección de un retorno tras inactividad, el agente impone los siguientes límites de volumen:
- Semana 1: Reducción del 50% respecto al volumen máximo registrado.
- Semana 2: Reducción del 30% respecto al volumen máximo registrado.
- Semana 3: Reducción del 20% respecto al volumen máximo registrado.
- Semana 4: Reducción del 10% respecto al volumen máximo registrado.

## 2. Monitorización de Umbrales Biométricos
El análisis de la base de datos kinetic_guard.db se rige por los siguientes parámetros de alerta:

| Parámetro | Valor Crítico | Respuesta del Sistema | Justificación Técnica |
| :--- | :--- | :--- | :--- |
| Descanso | Menor a 7 horas | Recomendación de ajuste de carga | El sueño insuficiente es el principal predictor de fatiga nerviosa. |
| Esfuerzo (RPE) | Superior a 7/10 | Consulta automática de protocolos | Prevención de cuadros de sobreentrenamiento y daño muscular. |
| HRV | Descenso significativo | Alerta de fatiga autonómica | Indicador de estrés en el sistema nervioso autónomo. |

## 3. Identificación de Patologías Críticas (Red Flags)
El sistema está configurado para detectar indicadores de condiciones médicas graves mediante el análisis de lenguaje natural y métricas de esfuerzo extremo.

### Rabdomiólisis Exergónica (ER)
Se activa ante la concurrencia de esfuerzo máximo (RPE 10), dolor muscular agudo y sintomatología específica como orina hipercromática (color té). La instrucción del sistema es el cese inmediato de la actividad y la derivación a servicios de urgencias.

### Golpe de Calor por Esfuerzo (EHS)
Identificado mediante la combinación de alta intensidad tras periodos de inactividad. El sistema instruye la activación del Plan de Acción de Emergencia (EAP) y protocolos de enfriamiento por inmersión.

## 4. Responsabilidad Profesional y Estándar de Cuidado
El funcionamiento del agente se alinea con el Estándar 1.2 de la NSCA. El sistema actúa como una herramienta de apoyo a la toma de decisiones, asumiendo que la seguridad del atleta es una responsabilidad conjunta entre el profesional certificado y la institución.
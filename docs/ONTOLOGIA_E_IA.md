# Descubrir primero, clasificar después

Cinco categorías de limpieza no son una ontología suficiente para un histórico personal de 30.000 mensajes. El flujo recomendado es estudiar el conjunto antes de decidir carpetas.

## Dos ejes independientes

Un mismo mensaje puede recibir:

```text
Organizador/
  Temas/
    Finanzas/
      Facturas
    Viajes/
      Reservas
  Entidades/
    proveedor.example
  Revisar para borrar
```

Los temas responden a «de qué trata»; las entidades a «con quién». Gmail permite ambas etiquetas en un mismo correo, sin duplicarlo. Las entidades actuales son dominios de remitente, no organizaciones verificadas. No se fusionan dominios automáticamente ni se confía en el nombre visible del remitente.

## 1. Importar e inventariar todo

Después de `gmail-sync`, desde la carpeta del proyecto:

```sh
python -m email_organizer.cli inventory
```

Genera `data/inventory.json`: cuenta todos los mensajes importados, dominios y grupos de asunto idéntico por dominio. Es un archivo privado. La cobertura se refiere a la base importada, no garantiza que la importación del buzón haya terminado: espera a que `gmail-sync` termine antes de empezar.

## 2. Descubrir una ontología con IA

Es opcional y requiere una clave API propia de OpenAI o Anthropic. Una suscripción de chat no sustituye a esa clave. Define `EMAIL_ORGANIZER_AI_KEY` en el entorno de tu terminal local, sin escribirla en archivos del repositorio, historial compartido ni capturas. No se incluye ninguna clave en el código.

Usa un modelo que tu cuenta admita y que soporte salida JSON. Sustituye `TU_MODELO` por su identificador real:

```sh
python -m email_organizer.cli ai-ontology --provider openai --model TU_MODELO --max-calls 10 --consent-send-headers
```

Para Claude, cambia el proveedor por `anthropic` y el modelo por un identificador de Anthropic.

**Datos enviados:** dominio del remitente, asunto truncado a 300 caracteres y frecuencia. Este paso incluye también los asuntos de mensajes protegidos; usa el indicador de consentimiento solo si autorizas esa transmisión. No envía direcciones completas, cuerpos ni adjuntos. Un asunto puede contener datos sensibles. La configuración de retención del proveedor depende de tu cuenta y contrato.

Se envían lotes de hasta 50 grupos: la IA propone una estructura y la revisa al recibir cada lote siguiente. Los grupos representan todos sus mensajes repetidos. El programa guarda después de cada llamada:

- Ontología propuesta, con un máximo de 60 hojas de dos niveles.
- Grupos y mensajes representados frente al total.
- `complete_headers`: si se han recorrido todos los grupos de cabeceras.
- `review_required`: la estructura todavía necesita revisión humana.

Si se agota `--max-calls`, el resultado es **parcial**. Repite el comando para continuar desde el último lote guardado. El máximo se aplica por ejecución; no es un límite en euros. Un histórico con 30.000 grupos únicos necesitaría hasta 600 llamadas de descubrimiento con lotes de 50. No hay que ejecutarlas sin estimar antes el coste del modelo. Si cambia la base o el modelo, utiliza otro `--output` para no mezclar análisis diferentes.

`complete_headers=true` no significa que se haya leído el contenido ni que la estructura sea óptima. El modelo recibe la ontología acumulada, no todos los lotes previos íntegros; puede perder categorías o matices. Revisa el resultado según tu uso real.

## 3. Revisar y fijar la ontología

Abre `data/ontology-draft.json`. Revisa `topics`, une categorías redundantes, corrige nombres y palabras clave; conserva la forma `Tema/Subtema`. Crea una copia como `data/ontology-approved.json` para trabajar con una versión estable. No cambies la taxonomía durante una misma ejecución de clasificación.

```sh
python -m email_organizer.cli classify --recalculate --taxonomy data/ontology-approved.json
```

Las reglas proponen temas por asunto. Si coinciden varias categorías o no hay evidencia, se asigna `Pendiente de revision`. No se fuerza una carpeta inventada para aparentar cobertura. La clasificación por reglas y los valores de confianza son heurísticos, no probabilidades calibradas.

Si omites `--taxonomy`, se utiliza un catálogo de ejemplo con 24 hojas: finanzas, compras, viajes, trabajo, educación, salud, hogar, cuentas, comunicaciones, personal y legal. Es un punto de partida, no una ontología descubierta de tu histórico.

Las entidades se proponen para los 50 dominios más frecuentes por cuenta, siempre que tengan al menos 20 mensajes. Ajusta con `--entity-min 20 --max-entities 50`. Esto limita la proliferación de carpetas. Se han añadido límites preventivos antes de acercarse al máximo de etiquetas de Gmail.

## 4. Resolver ambigüedades con IA

```sh
python -m email_organizer.cli ai-classify --provider openai --model TU_MODELO --taxonomy data/ontology-approved.json --max-calls 10 --consent-send-headers
python -m email_organizer.cli review
```

Esta fase solo envía asuntos ambiguos no protegidos, hasta 20 asuntos únicos por llamada. Usa caché por asunto, modelo y catálogo. No clasifica todo un remitente a partir de una muestra, porque una misma entidad puede mandar facturas, publicidad y alertas de seguridad. Los casos con confianza declarada inferior a 0,8 quedan pendientes. La IA no puede aprobar, archivar ni borrar: devuelve únicamente categorías del catálogo.

Revisa `tema`, `entidad`, `confianza` y `motivo_tema` en el CSV. Luego utiliza el mismo flujo `approve` → `gmail-apply --confirm`. Los mensajes protegidos reciben propuestas temáticas locales, pero siguen sin modificarse en Gmail. Volver a ejecutar `classify` rehace propuestas temáticas no aplicadas y elimina sus aprobaciones; hazlo antes de la revisión final, no después de aprobar.

## Qué faltaría para un sistema de conocimiento completo

La implementación actual trabaja con cabeceras. Todavía no descarga cuerpos, agrupa por conversaciones ni crea un índice semántico local. Para ese siguiente nivel conviene:

1. Descargar texto progresivamente, con consentimiento y almacenamiento local protegido.
2. Detectar entidades y conversaciones, y construir un índice semántico.
3. Descubrir temas sobre el histórico y validar la cobertura de cada grupo.
4. Comparar ontologías candidatas y medir ambigüedad y calidad con ejemplos revisados.
5. Reclasificar y mejorar reglas con las correcciones del usuario.

Los adjuntos pueden dejarse fuera inicialmente. Ni un modelo local ni uno externo garantizan una ontología perfecta sin validación. Este repositorio no presenta el análisis de cabeceras como un análisis completo del contenido.

## Validación disponible

Los flujos IA se prueban con respuestas simuladas: validación del catálogo, rechazo de salidas inválidas, límites de llamadas, caché, reanudación y cobertura. No se ha validado una cuenta real ni facturación de OpenAI/Anthropic. Los errores de red o respuestas JSON incompatibles detienen el proceso; los lotes ya guardados permanecen.

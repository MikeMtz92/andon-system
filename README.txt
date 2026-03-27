====================================================
         REACTION ANDON SYSTEM - GUÍA RÁPIDA
====================================================

📋 REQUISITOS DEL SISTEMA:
--------------------------
- Windows 10 u 11 (64 bits)
- 4GB RAM mínimo
- 500MB espacio en disco
- MySQL Server 5.7 o superior
- Conexión a internet (para primera activación)

🚀 INSTALACIÓN:
---------------
1. Ejecuta ReActionAndon_Setup.exe como Administrador
2. Sigue los pasos del asistente de instalación
3. Cuando termine, el programa se iniciará automáticamente

🔧 PRIMER USO:
--------------
Al ejecutar el programa por primera vez:

1. ACTIVACIÓN DE LICENCIA:
   - Ingresa tu clave de licencia (si tienes una)
   - O selecciona "Iniciar Demo" para probar 15 días

2. CONFIGURACIÓN MYSQL:
   - Ingresa los datos de tu servidor MySQL
   - La base de datos ya debe estar creada 'andon_db'
   - Por defecto: localhost, puerto 3306, usuario root, sin contraseña 
		(puedes personalizarlos en tu base de datos)


3. ¡LISTO! El sistema creará todas las tablas necesarias

📊 FUNCIONALIDADES PRINCIPALES:
-------------------------------
• Andon en Vivo: Visualiza y gestiona fallas en tiempo real
• Historial: Consulta todas las fallas registradas
• Proyección: Vista ampliada para pantallas externas
• Estadísticas: Gráficas y análisis detallados
• Configuración: Personaliza colores, tipos de falla y más
• Código ESP32: Genera firmware para dispositivos físicos

🆘 SOLUCIÓN DE PROBLEMAS:
-------------------------
❌ "No se puede conectar a MySQL":
   • Verifica que MySQL esté instalado y corriendo
   • Abre Services.msc y busca "MySQL", inicia el servicio
   • Verifica usuario/contraseña

❌ "Error al validar licencia":
   • Verifica tu conexión a internet
   • Asegura que la licencia sea correcta
   • El firewall podría estar bloqueando el puerto 3306

❌ El programa no inicia:
   • Ejecuta como Administrador
   • Verifica que no haya antivirus bloqueando
   • Revisa los logs en la consola (versión DEBUG)

📞 CONTACTO Y SOPORTE:
----------------------
Email: contacto@monsterweb.com.mx
Web: monsterweb.com.mx
Teléfono: +52 844 666 6607

====================================================
      © 2024 Monsterweb - Versión 1.0
====================================================
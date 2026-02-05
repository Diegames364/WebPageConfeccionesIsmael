document.addEventListener('DOMContentLoaded', function() {
    // 1. RECUPERAR LOS DATOS DEL HTML
    const dataScript = document.getElementById('chart-data-source');
    
    if (!dataScript) {
        console.error("No se encontraron datos para los gráficos.");
        return;
    }

    const rawData = JSON.parse(dataScript.textContent);

    const datosGraficos = {
        productosLabels: JSON.parse(rawData.productos_labels),
        productosData: JSON.parse(rawData.productos_data),
        estadosLabels: JSON.parse(rawData.estados_labels),
        estadosData: JSON.parse(rawData.estados_data)
    };

    // 2. CONFIGURACIÓN DEL GRÁFICO DE BARRAS (PRODUCTOS)
    const ctxProductos = document.getElementById('chartProductos').getContext('2d');
    new Chart(ctxProductos, {
        type: 'bar',
        data: {
            labels: datosGraficos.productosLabels,
            datasets: [{
                label: 'Unidades Vendidas',
                data: datosGraficos.productosData,
                backgroundColor: 'rgba(54, 162, 235, 0.6)', 
                borderColor: 'rgba(54, 162, 235, 1)',      
                borderWidth: 1,
                borderRadius: 5 
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false } 
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    ticks: { stepSize: 1 } 
                }
            }
        }
    });

    // 3. CONFIGURACIÓN DEL GRÁFICO DE DONA (ESTADOS)
    const ctxEstados = document.getElementById('chartEstados').getContext('2d');
    new Chart(ctxEstados, {
        type: 'doughnut',
        data: {
            labels: datosGraficos.estadosLabels,
            datasets: [{
                data: datosGraficos.estadosData,
                backgroundColor: [
                    '#ffc107', // Pendiente (Amarillo)
                    '#17a2b8', // Confirmado (Azul Cian)
                    '#6610f2', // Preparando (Morado)
                    '#fd7e14', // Enviado (Naranja)
                    '#28a745', // Entregado (Verde)
                    '#dc3545'  // Cancelado (Rojo)
                ],
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom', 
                    labels: { boxWidth: 12, padding: 20 }
                }
            }
        }
    });
});
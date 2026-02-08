// users/static/js/satellite_realtime.js

class SatelliteRealtime {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.stations = {};
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.startDataPolling();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/satellite/data/`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('📡 Connecté au simulateur satellite');
            this.connected = true;
            this.ws.send(JSON.stringify({ type: 'get_initial_data' }));
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            console.log('📡 Déconnecté du simulateur');
            this.connected = false;
            // Reconnexion après 5 secondes
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
            console.error('📡 Erreur WebSocket:', error);
        };
    }

    handleMessage(data) {
        switch(data.type) {
            case 'initial_data':
                this.stations = {};
                data.data.forEach(station => {
                    this.stations[station.id] = station;
                });
                this.updateDashboard();
                break;

            case 'new_data':
                data.data.forEach(update => {
                    const stationId = update.station_id;
                    if (this.stations[stationId]) {
                        if (!this.stations[stationId].last_data) {
                            this.stations[stationId].last_data = {};
                        }
                        Object.assign(this.stations[stationId].last_data, update.data);
                        this.stations[stationId].last_data.timestamp = update.timestamp;

                        // Mettre à jour l'affichage pour cette station
                        this.updateStationDisplay(stationId);
                    }
                });
                break;
        }
    }

    updateDashboard() {
        // Mettre à jour les statistiques
        const totalStations = Object.keys(this.stations).length;
        const activeStations = Object.values(this.stations).filter(s => s.status === 'ACTIF').length;

        // Mettre à jour les compteurs
        this.updateCounter('total-stations', totalStations);
        this.updateCounter('active-stations', activeStations);
        this.updateCounter('active-percentage',
            totalStations > 0 ? Math.round((activeStations / totalStations) * 100) : 0);

        // Mettre à jour le tableau des données
        this.updateDataTable();
    }

    updateStationDisplay(stationId) {
        const station = this.stations[stationId];
        if (!station) return;

        // Trouver toutes les cellules pour cette station
        const cells = document.querySelectorAll(`[data-station-id="${stationId}"]`);
        cells.forEach(cell => {
            const dataType = cell.getAttribute('data-data-type');
            if (dataType && station.last_data && station.last_data[dataType] !== undefined) {
                const value = station.last_data[dataType];
                cell.textContent = value !== null ? value.toFixed(1) : '-';
                cell.classList.add('updated');
                setTimeout(() => cell.classList.remove('updated'), 1000);
            }

            // Mettre à jour l'horodatage
            const timestampCells = document.querySelectorAll(`[data-station-timestamp="${stationId}"]`);
            if (station.last_data && station.last_data.timestamp) {
                const date = new Date(station.last_data.timestamp);
                timestampCells.forEach(cell => {
                    cell.textContent = date.toLocaleTimeString();
                    cell.classList.add('updated');
                    setTimeout(() => cell.classList.remove('updated'), 1000);
                });
            }
        });
    }

    updateDataTable() {
        const tbody = document.querySelector('#realtime-data tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        Object.values(this.stations).forEach(station => {
            const row = document.createElement('tr');

            // Date
            const dateCell = document.createElement('td');
            if (station.last_data && station.last_data.timestamp) {
                const date = new Date(station.last_data.timestamp);
                dateCell.textContent = date.toLocaleString();
            } else {
                dateCell.textContent = 'Jamais';
            }
            row.appendChild(dateCell);

            // Nom station
            const nameCell = document.createElement('td');
            nameCell.textContent = station.name;
            row.appendChild(nameCell);

            // Température
            const tempCell = document.createElement('td');
            tempCell.setAttribute('data-station-id', station.id);
            tempCell.setAttribute('data-data-type', 'temperature');
            tempCell.textContent = station.last_data && station.last_data.temperature !== undefined
                ? station.last_data.temperature.toFixed(1) : '-';
            row.appendChild(tempCell);

            // Pression
            const pressureCell = document.createElement('td');
            pressureCell.setAttribute('data-station-id', station.id);
            pressureCell.setAttribute('data-data-type', 'pressure');
            pressureCell.textContent = station.last_data && station.last_data.pressure !== undefined
                ? station.last_data.pressure.toFixed(1) : '-';
            row.appendChild(pressureCell);

            // Vent
            const windCell = document.createElement('td');
            windCell.setAttribute('data-station-id', station.id);
            windCell.setAttribute('data-data-type', 'wind');
            windCell.textContent = station.last_data && station.last_data.wind !== undefined
                ? station.last_data.wind.toFixed(1) : '-';
            row.appendChild(windCell);

            // Précipitations
            const precipCell = document.createElement('td');
            precipCell.setAttribute('data-station-id', station.id);
            precipCell.setAttribute('data-data-type', 'precipitation');
            precipCell.textContent = station.last_data && station.last_data.precipitation !== undefined
                ? station.last_data.precipitation.toFixed(1) : '-';
            row.appendChild(precipCell);

            // Ensoleillement
            const sunCell = document.createElement('td');
            sunCell.setAttribute('data-station-id', station.id);
            sunCell.setAttribute('data-data-type', 'sunshine');
            sunCell.textContent = station.last_data && station.last_data.sunshine !== undefined
                ? station.last_data.sunshine.toFixed(1) : '-';
            row.appendChild(sunCell);

            tbody.appendChild(row);
        });
    }

    updateCounter(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            const oldValue = parseInt(element.textContent) || 0;
            if (oldValue !== value) {
                element.textContent = value;
                element.classList.add('updated');
                setTimeout(() => element.classList.remove('updated'), 1000);
            }
        }
    }

    setupEventListeners() {
        // Rafraîchissement manuel
        document.getElementById('refresh-data')?.addEventListener('click', () => {
            if (this.connected) {
                this.ws.send(JSON.stringify({ type: 'get_initial_data' }));
            }
        });
    }

    startDataPolling() {
        // Fallback AJAX si WebSocket échoue
        setInterval(() => {
            if (!this.connected) {
                this.fetchLatestData();
            }
        }, 5000);
    }

    fetchLatestData() {
        fetch('/api/data/recent/')
            .then(response => response.json())
            .then(data => {
                this.updateFromApi(data);
            })
            .catch(error => console.error('Erreur fetch:', error));
    }

    updateFromApi(data) {
        // Mettre à jour avec les données API
        data.forEach(item => {
            const stationId = item.station_id;
            if (this.stations[stationId]) {
                if (!this.stations[stationId].last_data) {
                    this.stations[stationId].last_data = {};
                }
                this.stations[stationId].last_data = {
                    temperature: item.temperature,
                    pressure: item.pression,
                    wind: item.vitesse_vent,
                    precipitation: item.precipitation,
                    sunshine: item.ensoleillement,
                    timestamp: item.timestamp
                };
                this.updateStationDisplay(stationId);
            }
        });
    }
}

// Démarrer quand la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    window.satelliteRealtime = new SatelliteRealtime();
});

// users/static/js/auto_refresh.js

(function() {
    'use strict';

    // Configuration
    const REFRESH_INTERVAL = 15000; // 15 secondes en millisecondes
    let refreshTimer = null;

    // Fonction pour rafraîchir la page
    function refreshPage() {
        console.log('🔄 Rafraîchissement automatique de la page...');
        window.location.reload();
    }

    // Fonction pour démarrer le rafraîchissement automatique
    function startAutoRefresh() {
        // Arrêter le timer existant s'il y en a un
        if (refreshTimer) {
            clearTimeout(refreshTimer);
        }

        // Démarrer le nouveau timer
        refreshTimer = setTimeout(refreshPage, REFRESH_INTERVAL);

        // Afficher le prochain rafraîchissement dans la console
        const nextRefresh = new Date(Date.now() + REFRESH_INTERVAL);
        console.log(`⏰ Prochain rafraîchissement à ${nextRefresh.toLocaleTimeString()}`);
    }

    // Fonction pour arrêter le rafraîchissement automatique
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearTimeout(refreshTimer);
            refreshTimer = null;
            console.log('⏹️ Rafraîchissement automatique arrêté');
        }
    }

    // Fonction pour ajouter l'indicateur visuel
    function addRefreshIndicator() {
        // Créer l'indicateur
        const indicator = document.createElement('div');
        indicator.id = 'refresh-indicator';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #007bff;
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 9999;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        `;

        // Ajouter l'icône
        const icon = document.createElement('span');
        icon.innerHTML = '🔄';
        indicator.appendChild(icon);

        // Ajouter le texte
        const text = document.createElement('span');
        text.id = 'refresh-timer';
        text.textContent = '15s';
        indicator.appendChild(text);

        // Ajouter au body
        document.body.appendChild(indicator);

        // Mettre à jour le compte à rebours
        let secondsLeft = 15;
        const countdownInterval = setInterval(() => {
            secondsLeft--;
            text.textContent = `${secondsLeft}s`;

            if (secondsLeft <= 0) {
                secondsLeft = 15;
            }
        }, 1000);

        // Arrêter le rafraîchissement au clic
        indicator.addEventListener('click', function(e) {
            e.stopPropagation();
            if (confirm('Voulez-vous désactiver le rafraîchissement automatique ?')) {
                stopAutoRefresh();
                clearInterval(countdownInterval);
                indicator.style.display = 'none';
                // Stocker la préférence
                localStorage.setItem('autoRefreshDisabled', 'true');
            }
        });

        // Démarrer le compte à rebours pour l'indicateur
        return countdownInterval;
    }

    // Vérifier si l'utilisateur a désactivé le rafraîchissement
    function isRefreshDisabled() {
        return localStorage.getItem('autoRefreshDisabled') === 'true';
    }

    // Initialisation quand la page est chargée
    document.addEventListener('DOMContentLoaded', function() {
        // Ne pas rafraîchir sur les pages de formulaire (pour éviter de perdre les données)
        const hasForm = document.querySelector('form') !== null;
        const isLoginPage = window.location.pathname.includes('login');
        const isRegisterPage = window.location.pathname.includes('register');

        // Conditions pour ne pas rafraîchir
        if (isRefreshDisabled() || hasForm || isLoginPage || isRegisterPage) {
            console.log('⏸️ Rafraîchissement automatique désactivé pour cette page');
            return;
        }

        console.log('🚀 Rafraîchissement automatique activé (15 secondes)');

        // Démarrer le rafraîchissement
        startAutoRefresh();

        // Ajouter l'indicateur visuel
        addRefreshIndicator();

        // Redémarrer le timer quand la page devient visible (si l'utilisateur revient à l'onglet)
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden && !isRefreshDisabled()) {
                console.log('📱 Page visible, redémarrage du rafraîchissement');
                startAutoRefresh();
            }
        });
    });

    // Empêcher le rafraîchissement quand l'utilisateur interagit avec un formulaire
    document.addEventListener('focus', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            console.log('✏️ Saisie en cours, rafraîchissement temporairement désactivé');
            stopAutoRefresh();
        }
    }, true);

    document.addEventListener('blur', function(e) {
        if ((e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') && !isRefreshDisabled()) {
            console.log('✅ Saisie terminée, rafraîchissement réactivé');
            startAutoRefresh();
        }
    }, true);

    // Exposer les fonctions globalement (pour le debug)
    window.startAutoRefresh = startAutoRefresh;
    window.stopAutoRefresh = stopAutoRefresh;

})();
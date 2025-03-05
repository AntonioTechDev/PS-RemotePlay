"""
Modulo per il monitoraggio avanzato della rete e delle prestazioni della connessione.
"""
import socket
import time
import threading
import logging
import subprocess
import sys
import platform
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configurazione logging
logger = logging.getLogger("NetworkMonitor")

class NetworkMonitor:
    """Classe per monitorare la connessione di rete verso la console PlayStation."""
    
    def __init__(self, host: str, port: int = 9295, interval: float = 5.0):
        """
        Inizializza il monitor di rete.
        
        Args:
            host: L'indirizzo IP della console
            port: La porta da monitorare (default: 9295 per Remote Play)
            interval: Intervallo in secondi tra le verifiche
        """
        self.host = host
        self.port = port
        self.interval = interval
        self.is_running = False
        self.stats = {
            "ping_times": [],
            "connection_failures": 0,
            "last_check": None,
            "avg_ping": None,
            "max_ping": None,
            "min_ping": None,
            "packet_loss": 0
        }
        self._monitor_thread = None
        self._lock = threading.Lock()
    
    def _ping(self) -> Tuple[bool, Optional[float]]:
        """
        Esegue un ping verso la console e restituisce il tempo di risposta.
        
        Returns:
            Tupla (successo, tempo in ms)
        """
        system = platform.system().lower()
        
        try:
            if system == "windows":
                args = ["ping", "-n", "1", "-w", "1000", self.host]
            else:  # Linux, MacOS, etc.
                args = ["ping", "-c", "1", "-W", "1", self.host]
            
            start_time = time.time()
            result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            elapsed = (time.time() - start_time) * 1000  # ms
            
            if result.returncode == 0:
                # Estrai il tempo di ping effettivo dal risultato se possibile
                output = result.stdout
                if "time=" in output or "tempo=" in output:
                    # Cerca il tempo nel formato "time=1.2 ms" o simili
                    for line in output.splitlines():
                        if "time=" in line or "tempo=" in line:
                            parts = line.split("time=")
                            if len(parts) > 1:
                                try:
                                    # Estrai il numero prima di "ms"
                                    ping_time = float(parts[1].split("ms")[0].strip())
                                    return True, ping_time
                                except (ValueError, IndexError):
                                    pass
                
                # Se non riesci a estrarre il tempo esatto, usa il tempo misurato
                return True, elapsed
            
            return False, None
        
        except Exception as e:
            logger.error(f"Errore durante il ping: {e}")
            return False, None
    
    def _check_port(self) -> bool:
        """
        Verifica se la porta è raggiungibile.
        
        Returns:
            True se la porta è aperta, False altrimenti
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = False
        
        try:
            result = sock.connect_ex((self.host, self.port)) == 0
        except Exception as e:
            logger.error(f"Errore durante la verifica della porta: {e}")
        finally:
            sock.close()
        
        return result
    
    def _monitor_loop(self):
        """Loop di monitoraggio della connessione."""
        while self.is_running:
            try:
                ping_success, ping_time = self._ping()
                port_open = self._check_port()
                
                with self._lock:
                    self.stats["last_check"] = datetime.now()
                    
                    if ping_success and ping_time is not None:
                        self.stats["ping_times"].append(ping_time)
                        # Mantieni solo gli ultimi 10 valori
                        if len(self.stats["ping_times"]) > 10:
                            self.stats["ping_times"].pop(0)
                        
                        # Aggiorna le statistiche
                        self.stats["avg_ping"] = sum(self.stats["ping_times"]) / len(self.stats["ping_times"])
                        self.stats["max_ping"] = max(self.stats["ping_times"])
                        self.stats["min_ping"] = min(self.stats["ping_times"])
                    
                    if not ping_success or not port_open:
                        self.stats["connection_failures"] += 1
                        
                        # Calcola la percentuale di pacchetti persi
                        total_checks = len(self.stats["ping_times"]) + self.stats["connection_failures"]
                        if total_checks > 0:
                            self.stats["packet_loss"] = (self.stats["connection_failures"] / total_checks) * 100
                
                # Log dello stato
                if ping_success and port_open:
                    logger.debug(f"✅ Connessione OK: Ping {ping_time:.1f}ms")
                else:
                    issues = []
                    if not ping_success:
                        issues.append("ping fallito")
                    if not port_open:
                        issues.append("porta chiusa")
                    
                    logger.warning(f"⚠️ Problemi di connessione: {', '.join(issues)}")
            
            except Exception as e:
                logger.error(f"Errore nel loop di monitoraggio: {e}")
            
            time.sleep(self.interval)
    
    def start(self):
        """Avvia il monitoraggio della connessione in un thread separato."""
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            logger.warning("Il monitoraggio è già in esecuzione.")
            return
        
        self.is_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"🔍 Monitoraggio connessione avviato verso {self.host}:{self.port}")
    
    def stop(self):
        """Ferma il monitoraggio della connessione."""
        self.is_running = False
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=2.0)
        logger.info("🛑 Monitoraggio connessione arrestato")
    
    def get_status(self) -> Dict:
        """
        Restituisce lo stato attuale della connessione.
        
        Returns:
            Dict con le statistiche della connessione
        """
        with self._lock:
            return self.stats.copy()
    
    def is_connection_stable(self) -> Tuple[bool, str]:
        """
        Valuta se la connessione è stabile in base alle statistiche raccolte.
        
        Returns:
            Tupla (stabilità, messaggio)
        """
        with self._lock:
            if not self.stats["ping_times"]:
                return False, "Nessun dato di ping disponibile"
            
            avg_ping = self.stats.get("avg_ping", 0)
            packet_loss = self.stats.get("packet_loss", 0)
            
            if packet_loss > 20:
                return False, f"Perdita di pacchetti elevata: {packet_loss:.1f}%"
            
            if avg_ping > 100:
                return False, f"Ping medio elevato: {avg_ping:.1f}ms"
            
            return True, f"Connessione stabile: Ping {avg_ping:.1f}ms, Perdita {packet_loss:.1f}%"


class AsyncNetworkMonitor:
    """Versione asincrona del monitor di rete."""
    
    def __init__(self, host: str, port: int = 9295, interval: float = 5.0):
        """
        Inizializza il monitor di rete asincrono.
        
        Args:
            host: L'indirizzo IP della console
            port: La porta da monitorare (default: 9295 per Remote Play)
            interval: Intervallo in secondi tra le verifiche
        """
        self.host = host
        self.port = port
        self.interval = interval
        self.is_running = False
        self.stats = {
            "ping_times": [],
            "connection_failures": 0,
            "last_check": None,
            "avg_ping": None,
            "max_ping": None,
            "min_ping": None,
            "packet_loss": 0
        }
        self._monitor_task = None
        self._lock = asyncio.Lock()
    
    async def _async_ping(self) -> Tuple[bool, Optional[float]]:
        """
        Esegue un ping verso la console in modo asincrono.
        
        Returns:
            Tupla (successo, tempo in ms)
        """
        system = platform.system().lower()
        
        try:
            if system == "windows":
                args = ["ping", "-n", "1", "-w", "1000", self.host]
            else:  # Linux, MacOS, etc.
                args = ["ping", "-c", "1", "-W", "1", self.host]
            
            start_time = time.time()
            
            # Esegui il comando in modo asincrono
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = await process.communicate()
            elapsed = (time.time() - start_time) * 1000  # ms
            
            if process.returncode == 0:
                # Estrai il tempo di ping effettivo dal risultato se possibile
                output = stdout
                if "time=" in output or "tempo=" in output:
                    # Cerca il tempo nel formato "time=1.2 ms" o simili
                    for line in output.splitlines():
                        if "time=" in line or "tempo=" in line:
                            parts = line.split("time=")
                            if len(parts) > 1:
                                try:
                                    # Estrai il numero prima di "ms"
                                    ping_time = float(parts[1].split("ms")[0].strip())
                                    return True, ping_time
                                except (ValueError, IndexError):
                                    pass
                
                # Se non riesci a estrarre il tempo esatto, usa il tempo misurato
                return True, elapsed
            
            return False, None
        
        except Exception as e:
            logger.error(f"Errore durante il ping asincrono: {e}")
            return False, None
    
    async def _async_check_port(self) -> bool:
        """
        Verifica se la porta è raggiungibile in modo asincrono.
        
        Returns:
            True se la porta è aperta, False altrimenti
        """
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=1.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
        except Exception as e:
            logger.error(f"Errore durante la verifica asincrona della porta: {e}")
            return False
    
    async def _monitor_loop(self):
        """Loop asincrono di monitoraggio della connessione."""
        while self.is_running:
            try:
                ping_success, ping_time = await self._async_ping()
                port_open = await self._async_check_port()
                
                async with self._lock:
                    self.stats["last_check"] = datetime.now()
                    
                    if ping_success and ping_time is not None:
                        self.stats["ping_times"].append(ping_time)
                        # Mantieni solo gli ultimi 10 valori
                        if len(self.stats["ping_times"]) > 10:
                            self.stats["ping_times"].pop(0)
                        
                        # Aggiorna le statistiche
                        self.stats["avg_ping"] = sum(self.stats["ping_times"]) / len(self.stats["ping_times"])
                        self.stats["max_ping"] = max(self.stats["ping_times"])
                        self.stats["min_ping"] = min(self.stats["ping_times"])
                    
                    if not ping_success or not port_open:
                        self.stats["connection_failures"] += 1
                        
                        # Calcola la percentuale di pacchetti persi
                        total_checks = len(self.stats["ping_times"]) + self.stats["connection_failures"]
                        if total_checks > 0:
                            self.stats["packet_loss"] = (self.stats["connection_failures"] / total_checks) * 100
                
                # Log dello stato
                if ping_success and port_open:
                    logger.debug(f"✅ Connessione OK: Ping {ping_time:.1f}ms")
                else:
                    issues = []
                    if not ping_success:
                        issues.append("ping fallito")
                    if not port_open:
                        issues.append("porta chiusa")
                    
                    logger.warning(f"⚠️ Problemi di connessione: {', '.join(issues)}")
            
            except Exception as e:
                logger.error(f"Errore nel loop di monitoraggio asincrono: {e}")
            
            await asyncio.sleep(self.interval)
    
    async def start(self):
        """Avvia il monitoraggio asincrono della connessione."""
        if self.is_running:
            logger.warning("Il monitoraggio asincrono è già in esecuzione.")
            return
        
        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"🔍 Monitoraggio connessione asincrono avviato verso {self.host}:{self.port}")
    
    async def stop(self):
        """Ferma il monitoraggio asincrono della connessione."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Monitoraggio connessione asincrono arrestato")
    
    async def get_status(self) -> Dict:
        """
        Restituisce lo stato attuale della connessione.
        
        Returns:
            Dict con le statistiche della connessione
        """
        async with self._lock:
            return self.stats.copy()
    
    async def is_connection_stable(self) -> Tuple[bool, str]:
        """
        Valuta se la connessione è stabile in base alle statistiche raccolte.
        
        Returns:
            Tupla (stabilità, messaggio)
        """
        async with self._lock:
            if not self.stats["ping_times"]:
                return False, "Nessun dato di ping disponibile"
            
            avg_ping = self.stats.get("avg_ping", 0)
            packet_loss = self.stats.get("packet_loss", 0)
            
            if packet_loss > 20:
                return False, f"Perdita di pacchetti elevata: {packet_loss:.1f}%"
            
            if avg_ping > 100:
                return False, f"Ping medio elevato: {avg_ping:.1f}ms"
            
            return True, f"Connessione stabile: Ping {avg_ping:.1f}ms, Perdita {packet_loss:.1f}%"


# Funzione di utilità per verificare rapidamente lo stato di una connessione
async def check_connection(host: str, port: int = 9295) -> Dict:
    """
    Verifica rapidamente lo stato della connessione verso un host.
    
    Args:
        host: L'indirizzo IP dell'host
        port: La porta da verificare
        
    Returns:
        Dict con i risultati della verifica
    """
    monitor = AsyncNetworkMonitor(host, port)
    ping_success, ping_time = await monitor._async_ping()
    port_open = await monitor._async_check_port()
    
    return {
        "host": host,
        "port": port,
        "ping_success": ping_success,
        "ping_time": ping_time,
        "port_open": port_open,
        "timestamp": datetime.now()
    }
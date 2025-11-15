"""
Simulateur d'utilisateurs pour l'API de prédiction.

Ce module permet de simuler des charges de travail sur l'API
en envoyant des requêtes concurrentes avec des données aléatoires.

Supporte deux modes:
- HTTP: Requêtes directes via httpx (par défaut)
- Gradio: Requêtes via l'API Gradio (compatible HF Spaces)
"""

import asyncio
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel

try:
    from gradio_client import Client as GradioClient
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False


class SimulationConfig(BaseModel):
    """Configuration pour une simulation."""

    api_url: str = "http://localhost:8000"
    num_requests: int = 100
    concurrent_users: int = 10
    delay_between_requests: float = 0.0
    timeout: float = 30.0
    endpoint: str = "/predict"
    verbose: bool = False
    # Mode de simulation
    use_gradio: bool = False  # Si True, utilise l'API Gradio
    gradio_url: Optional[str] = None  # URL Gradio (ex: http://localhost:7860)
    hf_token: Optional[str] = None  # Token HuggingFace pour Spaces privés
    # Data drift sur l'âge
    enable_age_drift: bool = False
    age_drift_target_mean: float = 70.0
    age_drift_start_pct: float = 0.0
    age_drift_end_pct: float = 100.0

    class Config:
        """Configuration Pydantic."""

        arbitrary_types_allowed = True


@dataclass
class SimulationResult:
    """Résultats d'une simulation."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=dict)

    def __str__(self) -> str:
        """Format les résultats pour affichage."""
        return f"""
╔══════════════════════════════════════════════════════════╗
║           RÉSULTATS DE LA SIMULATION                     ║
╠══════════════════════════════════════════════════════════╣
║ Requêtes totales      : {self.total_requests:>10}            ║
║ Requêtes réussies     : {self.successful_requests:>10}            ║
║ Requêtes échouées     : {self.failed_requests:>10}            ║
║                                                          ║
║ Durée totale          : {self.total_duration:>10.2f} s         ║
║ Temps de réponse moy. : {self.avg_response_time:>10.2f} ms        ║
║ Temps de réponse min  : {self.min_response_time:>10.2f} ms        ║
║ Temps de réponse max  : {self.max_response_time:>10.2f} ms        ║
║                                                          ║
║ Requêtes par seconde  : {self.requests_per_second:>10.2f} req/s     ║
╚══════════════════════════════════════════════════════════╝

Status codes:
{self._format_status_codes()}

Erreurs: {len(self.errors)}
{self._format_errors()}
        """.strip()

    def _format_status_codes(self) -> str:
        """Format les status codes pour affichage."""
        if not self.status_codes:
            return "  Aucun"
        lines = []
        for code, count in sorted(self.status_codes.items()):
            lines.append(f"  {code}: {count}")
        return "\n".join(lines)

    def _format_errors(self) -> str:
        """Format les erreurs pour affichage."""
        if not self.errors:
            return ""
        # Afficher seulement les 5 premières erreurs
        errors_to_show = self.errors[:5]
        lines = [f"  - {error}" for error in errors_to_show]
        if len(self.errors) > 5:
            lines.append(f"  ... et {len(self.errors) - 5} autres")
        return "\n".join(lines)


class UserSimulator:
    """Simulateur d'utilisateurs pour l'API."""

    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialise le simulateur.

        Args:
            config: Configuration de la simulation.
        """
        self.config = config or SimulationConfig()
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.status_codes: Dict[int, int] = {}
        self.successful = 0
        self.failed = 0
        self.request_count = 0
        self.gradio_client = None

        # Initialiser le client Gradio si nécessaire
        if self.config.use_gradio:
            if not GRADIO_AVAILABLE:
                raise ImportError(
                    "gradio_client n'est pas installé. "
                    "Installez-le avec: pip install gradio-client"
                )
            gradio_url = self.config.gradio_url or "http://localhost:7860"
            hf_token = self.config.hf_token or os.environ.get("HF_TOKEN")
            self.gradio_client = GradioClient(gradio_url, hf_token=hf_token)

    def _calculate_age_with_drift(self) -> int:
        """
        Calcule l'âge avec drift progressif si activé.

        Le drift évolue linéairement entre drift_start_pct et drift_end_pct
        de la simulation, passant de la distribution normale (20-90)
        à une distribution centrée sur age_drift_target_mean.

        Returns:
            Âge du patient (entre 20 et 90).
        """
        if not self.config.enable_age_drift:
            return random.randint(20, 90)

        # Calculer le pourcentage de progression
        progress_pct = (
            (self.request_count / self.config.num_requests) * 100
            if self.config.num_requests > 0
            else 0
        )

        # Si on est avant le début du drift
        if progress_pct < self.config.age_drift_start_pct:
            return random.randint(20, 90)

        # Si on est après la fin du drift
        if progress_pct >= self.config.age_drift_end_pct:
            # Distribution normale centrée sur target_mean
            age = int(random.gauss(self.config.age_drift_target_mean, 10))
            return max(20, min(90, age))

        # Drift progressif entre start et end
        drift_progress = (
            (progress_pct - self.config.age_drift_start_pct) /
            (self.config.age_drift_end_pct - self.config.age_drift_start_pct)
        )

        # Mélange entre distribution uniforme et distribution avec drift
        if random.random() < drift_progress:
            # Distribution avec drift
            age = int(random.gauss(self.config.age_drift_target_mean, 10))
            return max(20, min(90, age))
        else:
            # Distribution normale originale
            return random.randint(20, 90)

    def generate_patient_data(self) -> Dict:
        """
        Génère des données de patient aléatoires.

        Returns:
            Dictionnaire avec les données du patient.
        """
        self.request_count += 1

        return {
            "AGE": self._calculate_age_with_drift(),
            "GENDER": random.randint(0, 1),
            "SMOKING": random.randint(0, 1),
            "ALCOHOL CONSUMING": random.randint(0, 1),
            "PEER_PRESSURE": random.randint(0, 1),
            "YELLOW_FINGERS": random.randint(0, 1),
            "ANXIETY": random.randint(0, 1),
            "FATIGUE": random.randint(0, 1),
            "ALLERGY": random.randint(0, 1),
            "WHEEZING": random.randint(0, 1),
            "COUGHING": random.randint(0, 1),
            "SHORTNESS OF BREATH": random.randint(0, 1),
            "SWALLOWING DIFFICULTY": random.randint(0, 1),
            "CHEST PAIN": random.randint(0, 1),
            "CHRONIC DISEASE": random.randint(0, 1),
        }

    def send_request_gradio(self, request_id: int) -> Dict:
        """
        Envoie une requête via l'API Gradio (mode synchrone).

        Args:
            request_id: Identifiant de la requête.

        Returns:
            Dictionnaire avec les résultats de la requête.
        """
        patient_data = self.generate_patient_data()

        start_time = time.time()
        result = {
            "request_id": request_id,
            "success": False,
            "response_time": 0.0,
            "status_code": 0,
            "error": None,
        }

        try:
            # Déterminer l'endpoint Gradio en fonction de l'endpoint FastAPI
            if "predict_proba" in self.config.endpoint:
                api_name = "/predict_proba_api"
            else:
                api_name = "/predict_api"

            # Envoyer la requête (résultat non utilisé, on mesure juste le temps)
            self.gradio_client.predict(
                patient_data,
                api_name=api_name
            )
            response_time = (time.time() - start_time) * 1000  # en ms

            result["success"] = True
            result["response_time"] = response_time
            result["status_code"] = 200

            if self.config.verbose:
                print(
                    f"Request {request_id}: "
                    f"200 - "
                    f"{response_time:.2f}ms"
                )

        except Exception as e:
            result["error"] = f"Erreur Gradio: {str(e)}"
            if self.config.verbose:
                print(f"Request {request_id}: Error - {str(e)}")

        finally:
            response_time = (time.time() - start_time) * 1000
            result["response_time"] = response_time

        return result

    async def send_request(
        self, client: httpx.AsyncClient, request_id: int
    ) -> Dict:
        """
        Envoie une requête à l'API.

        Args:
            client: Client HTTP asynchrone.
            request_id: Identifiant de la requête.

        Returns:
            Dictionnaire avec les résultats de la requête.
        """
        patient_data = self.generate_patient_data()
        url = f"{self.config.api_url}{self.config.endpoint}"

        start_time = time.time()
        result = {
            "request_id": request_id,
            "success": False,
            "response_time": 0.0,
            "status_code": 0,
            "error": None,
        }

        try:
            response = await client.post(
                url, json=patient_data, timeout=self.config.timeout
            )
            response_time = (time.time() - start_time) * 1000  # en ms

            result["success"] = response.status_code == 200
            result["response_time"] = response_time
            result["status_code"] = response.status_code

            if self.config.verbose:
                print(
                    f"Request {request_id}: "
                    f"{response.status_code} - "
                    f"{response_time:.2f}ms"
                )

        except httpx.TimeoutException:
            result["error"] = f"Timeout après {self.config.timeout}s"
            if self.config.verbose:
                print(f"Request {request_id}: Timeout")

        except httpx.ConnectError as e:
            result["error"] = f"Erreur de connexion: {str(e)}"
            if self.config.verbose:
                print(f"Request {request_id}: Connection error")

        except Exception as e:
            result["error"] = f"Erreur: {str(e)}"
            if self.config.verbose:
                print(f"Request {request_id}: Error - {str(e)}")

        finally:
            response_time = (time.time() - start_time) * 1000
            result["response_time"] = response_time

        return result

    async def run_batch(
        self, client: httpx.AsyncClient, start_id: int, batch_size: int
    ) -> List[Dict]:
        """
        Execute un lot de requêtes.

        Args:
            client: Client HTTP asynchrone.
            start_id: ID de départ pour les requêtes.
            batch_size: Nombre de requêtes dans le lot.

        Returns:
            Liste des résultats.
        """
        tasks = []
        for i in range(batch_size):
            request_id = start_id + i
            task = self.send_request(client, request_id)
            tasks.append(task)

            # Délai entre les requêtes si configuré
            if self.config.delay_between_requests > 0:
                await asyncio.sleep(self.config.delay_between_requests)

        results = await asyncio.gather(*tasks)
        return results

    def run_batch_gradio(
        self, start_id: int, batch_size: int
    ) -> List[Dict]:
        """
        Execute un lot de requêtes via Gradio (synchrone).

        Args:
            start_id: ID de départ pour les requêtes.
            batch_size: Nombre de requêtes dans le lot.

        Returns:
            Liste des résultats.
        """
        results = []
        with ThreadPoolExecutor(
            max_workers=self.config.concurrent_users
        ) as executor:
            futures = []
            for i in range(batch_size):
                request_id = start_id + i
                future = executor.submit(self.send_request_gradio, request_id)
                futures.append(future)

                # Délai entre les requêtes si configuré
                if self.config.delay_between_requests > 0:
                    time.sleep(self.config.delay_between_requests)

            # Récupérer tous les résultats
            for future in futures:
                results.append(future.result())

        return results

    def run_simulation_gradio(self) -> SimulationResult:
        """
        Execute la simulation complète en mode Gradio (synchrone).

        Returns:
            SimulationResult avec les résultats de la simulation.
        """
        print("\n🚀 Démarrage de la simulation (mode Gradio)...")
        gradio_url = self.config.gradio_url or "http://localhost:7860"
        print(f"   Gradio: {gradio_url}")
        print(f"   Endpoint: {self.config.endpoint}")
        print(f"   Requêtes: {self.config.num_requests}")
        print(f"   Utilisateurs concurrents: {self.config.concurrent_users}")
        print()

        start_time = time.time()

        # Diviser les requêtes en lots selon le nombre d'utilisateurs
        batch_size = self.config.concurrent_users
        num_batches = (
            self.config.num_requests + batch_size - 1
        ) // batch_size

        all_results = []
        for batch_num in range(num_batches):
            start_id = batch_num * batch_size
            remaining = self.config.num_requests - start_id
            current_batch_size = min(batch_size, remaining)

            if self.config.verbose:
                print(
                    f"\n📦 Lot {batch_num + 1}/{num_batches} "
                    f"({current_batch_size} requêtes)"
                )

            batch_results = self.run_batch_gradio(
                start_id, current_batch_size
            )
            all_results.extend(batch_results)

            # Afficher progression
            progress = len(all_results) / self.config.num_requests * 100
            print(f"   Progression: {progress:.1f}% ", end="\r")

        total_duration = time.time() - start_time

        # Analyser les résultats
        for result in all_results:
            self.response_times.append(result["response_time"])

            if result["success"]:
                self.successful += 1
            else:
                self.failed += 1
                if result["error"]:
                    self.errors.append(result["error"])

            status_code = result["status_code"]
            if status_code > 0:
                self.status_codes[status_code] = (
                    self.status_codes.get(status_code, 0) + 1
                )

        # Calculer les statistiques
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times
            else 0
        )
        min_response_time = min(self.response_times) if self.response_times else 0  # noqa: E501
        max_response_time = max(self.response_times) if self.response_times else 0  # noqa: E501
        rps = self.config.num_requests / total_duration if total_duration > 0 else 0  # noqa: E501

        return SimulationResult(
            total_requests=self.config.num_requests,
            successful_requests=self.successful,
            failed_requests=self.failed,
            total_duration=total_duration,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=rps,
            response_times=self.response_times,
            errors=self.errors,
            status_codes=self.status_codes,
        )

    async def run_simulation(self) -> SimulationResult:
        """
        Execute la simulation complète.

        Returns:
            SimulationResult avec les résultats de la simulation.
        """
        print("\n🚀 Démarrage de la simulation...")
        print(f"   API: {self.config.api_url}{self.config.endpoint}")
        print(f"   Requêtes: {self.config.num_requests}")
        print(f"   Utilisateurs concurrents: {self.config.concurrent_users}")
        print()

        start_time = time.time()

        async with httpx.AsyncClient() as client:
            # Diviser les requêtes en lots selon le nombre d'utilisateurs
            batch_size = self.config.concurrent_users
            num_batches = (
                self.config.num_requests + batch_size - 1
            ) // batch_size

            all_results = []
            for batch_num in range(num_batches):
                start_id = batch_num * batch_size
                remaining = self.config.num_requests - start_id
                current_batch_size = min(batch_size, remaining)

                if self.config.verbose:
                    print(
                        f"\n📦 Lot {batch_num + 1}/{num_batches} "
                        f"({current_batch_size} requêtes)"
                    )

                batch_results = await self.run_batch(
                    client, start_id, current_batch_size
                )
                all_results.extend(batch_results)

                # Afficher progression
                progress = len(all_results) / self.config.num_requests * 100
                print(f"   Progression: {progress:.1f}% ", end="\r")

        total_duration = time.time() - start_time

        # Analyser les résultats
        for result in all_results:
            self.response_times.append(result["response_time"])

            if result["success"]:
                self.successful += 1
            else:
                self.failed += 1
                if result["error"]:
                    self.errors.append(result["error"])

            status_code = result["status_code"]
            if status_code > 0:
                self.status_codes[status_code] = (
                    self.status_codes.get(status_code, 0) + 1
                )

        # Calculer les statistiques
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times
            else 0
        )
        min_response_time = min(self.response_times) if self.response_times else 0  # noqa: E501
        max_response_time = max(self.response_times) if self.response_times else 0  # noqa: E501
        rps = self.config.num_requests / total_duration if total_duration > 0 else 0  # noqa: E501

        return SimulationResult(
            total_requests=self.config.num_requests,
            successful_requests=self.successful,
            failed_requests=self.failed,
            total_duration=total_duration,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=rps,
            response_times=self.response_times,
            errors=self.errors,
            status_codes=self.status_codes,
        )

    def run(self) -> SimulationResult:
        """
        Lance la simulation (version synchrone).

        Returns:
            SimulationResult avec les résultats.
        """
        if self.config.use_gradio:
            return self.run_simulation_gradio()
        else:
            return asyncio.run(self.run_simulation())

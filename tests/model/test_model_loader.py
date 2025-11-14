"""
Tests unitaires pour le module ModelLoader.

Ce module teste:
- ModelLoader.__new__() (Singleton)
- ModelLoader.load_model()
- ModelLoader.model (property)
- ModelLoader.is_loaded()
"""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.model.model_loader import ModelLoader


@pytest.fixture(autouse=True)
def reset_model_loader():
    """Reset ModelLoader singleton avant et après chaque test."""
    ModelLoader._instance = None
    ModelLoader._model = None
    yield
    ModelLoader._instance = None
    ModelLoader._model = None


class TestSingleton:
    """Tests pour le pattern Singleton."""

    def test_singleton_returns_same_instance(self):
        """Test que ModelLoader retourne toujours la même instance."""
        loader1 = ModelLoader()
        loader2 = ModelLoader()

        assert loader1 is loader2

    def test_singleton_shares_model(self):
        """Test que les instances partagent le même modèle."""
        loader1 = ModelLoader()
        mock_model = MagicMock()
        loader1._model = mock_model

        loader2 = ModelLoader()
        assert loader2._model is mock_model


class TestIsLoaded:
    """Tests pour la méthode is_loaded()."""

    def test_is_loaded_returns_false_initially(self):
        """Test que is_loaded retourne False au départ."""
        loader = ModelLoader()
        assert loader.is_loaded() is False

    def test_is_loaded_returns_true_after_loading(self):
        """Test que is_loaded retourne True après chargement."""
        loader = ModelLoader()
        loader._model = MagicMock()
        assert loader.is_loaded() is True

    def test_is_loaded_returns_false_when_none(self):
        """Test que is_loaded retourne False si _model est None."""
        loader = ModelLoader()
        loader._model = None
        assert loader.is_loaded() is False


class TestModelProperty:
    """Tests pour la propriété model."""

    def test_model_returns_loaded_model(self):
        """Test que model retourne le modèle chargé."""
        loader = ModelLoader()
        mock_model = MagicMock()
        loader._model = mock_model

        assert loader.model is mock_model

    def test_model_raises_error_when_not_loaded(self):
        """Test que model lève une erreur si non chargé."""
        loader = ModelLoader()

        with pytest.raises(RuntimeError, match="modèle n'a pas été chargé"):
            _ = loader.model


class TestLoadModel:
    """Tests pour la méthode load_model()."""

    def test_load_model_returns_cached_model(self):
        """Test que load_model retourne le modèle en cache."""
        loader = ModelLoader()
        mock_model = MagicMock()
        loader._model = mock_model

        result = loader.load_model()
        assert result is mock_model

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_load_model_loads_from_file(
        self, mock_pickle_load, mock_file, mock_exists
    ):
        """Test que load_model charge depuis le fichier."""
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_pickle_load.return_value = mock_model

        loader = ModelLoader()
        result = loader.load_model("test_model.pkl")

        assert result is mock_model
        assert loader._model is mock_model
        mock_pickle_load.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_model_raises_error_if_file_not_found(self, mock_exists):
        """Test que load_model lève une erreur si fichier absent."""
        mock_exists.return_value = False

        loader = ModelLoader()

        with pytest.raises(
            FileNotFoundError,
            match="fichier du modèle n'existe pas"
        ):
            loader.load_model("nonexistent.pkl")

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_load_model_raises_error_on_pickle_failure(
        self, mock_pickle_load, mock_file, mock_exists
    ):
        """Test que load_model lève une erreur si pickle échoue."""
        mock_exists.return_value = True
        mock_pickle_load.side_effect = Exception("Pickle error")

        loader = ModelLoader()

        with pytest.raises(
            Exception,
            match="Erreur lors du chargement du modèle"
        ):
            loader.load_model("bad_model.pkl")

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('src.config.settings')
    def test_load_model_uses_default_path(
        self, mock_settings, mock_pickle_load, mock_file, mock_exists
    ):
        """Test que load_model utilise le chemin par défaut."""
        mock_exists.return_value = True
        mock_settings.MODEL_PATH = "./model/model.pkl"
        mock_model = MagicMock()
        mock_pickle_load.return_value = mock_model

        loader = ModelLoader()
        result = loader.load_model()

        assert result is mock_model


class TestEdgeCases:
    """Tests de cas limites."""

    def test_multiple_load_calls_return_same_model(self):
        """Test que plusieurs appels load_model retournent le même."""
        loader = ModelLoader()
        mock_model = MagicMock()
        loader._model = mock_model

        result1 = loader.load_model()
        result2 = loader.load_model()

        assert result1 is result2
        assert result1 is mock_model

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_absolute_path_handling(
        self, mock_pickle_load, mock_file, mock_exists
    ):
        """Test gestion des chemins absolus."""
        mock_exists.return_value = True
        mock_model = MagicMock()
        mock_pickle_load.return_value = mock_model

        loader = ModelLoader()
        absolute_path = "/absolute/path/to/model.pkl"
        result = loader.load_model(absolute_path)

        assert result is mock_model

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_absolute')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_relative_path_handling(
        self, mock_pickle_load, mock_file, mock_is_abs, mock_exists
    ):
        """Test gestion des chemins relatifs."""
        mock_exists.return_value = True
        mock_is_abs.return_value = False
        mock_model = MagicMock()
        mock_pickle_load.return_value = mock_model

        loader = ModelLoader()
        result = loader.load_model("./relative/model.pkl")

        assert result is mock_model

#!/usr/bin/env python3
"""
Script de conversion du modèle scikit-learn vers ONNX.

Ce script convertit le modèle ML au format ONNX (Open Neural Network Exchange)
pour améliorer la portabilité, les performances et éviter les problèmes
de sécurité liés à pickle.

Avantages ONNX:
- Format ouvert et standardisé
- Performances optimisées (runtime ONNX plus rapide)
- Portabilité multi-plateforme
- Pas de problèmes de sécurité pickle
- Compatible avec de nombreux frameworks

Usage:
    python scripts/convert_to_onnx.py [--input MODEL_PATH] [--output ONNX_PATH]

Exemples:
    # Conversion standard
    python scripts/convert_to_onnx.py

    # Avec chemins personnalisés
    python scripts/convert_to_onnx.py --input model/model.pkl \\
        --output model/model.onnx

    # Avec validation
    python scripts/convert_to_onnx.py --validate

Requirements:
    pip install onnx onnxruntime skl2onnx
"""

import argparse
import pickle
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# Register LightGBM converter if available
try:
    import lightgbm
    from skl2onnx import update_registered_converter
    from skl2onnx.common.shape_calculator import (
        calculate_linear_classifier_output_shapes
    )
    from onnxmltools.convert.lightgbm.operator_converters.LightGbm import (
        convert_lightgbm
    )

    # Register the LightGBM converter for sklearn-onnx
    update_registered_converter(
        lightgbm.LGBMClassifier,
        'LightGbmLGBMClassifier',
        calculate_linear_classifier_output_shapes,
        convert_lightgbm,
        options={'nocl': [True, False], 'zipmap': [True, False, 'columns']}
    )
    LIGHTGBM_AVAILABLE = True
    print("✅ LightGBM converter enregistré")
except ImportError as e:
    LIGHTGBM_AVAILABLE = False
    print(f"⚠️  Erreur d'import LightGBM converter: {e}")
    print("   Installez avec: uv add onnxmltools")


def load_pickle_model(model_path: str):
    """
    Charge le modèle depuis un fichier pickle.

    Args:
        model_path: Chemin vers le fichier .pkl

    Returns:
        Le modèle chargé

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        Exception: Si le chargement échoue
    """
    model_file = Path(model_path)
    if not model_file.exists():
        raise FileNotFoundError(f"Modèle non trouvé: {model_path}")

    print(f"📦 Chargement du modèle depuis {model_path}...")
    with open(model_file, "rb") as f:
        model = pickle.load(f)

    print(f"✅ Modèle chargé: {type(model).__name__}")
    return model


def get_model_info(model) -> dict:
    """
    Récupère les informations du modèle.

    Args:
        model: Le modèle scikit-learn

    Returns:
        Dictionnaire avec les informations du modèle
    """
    info = {
        "type": type(model).__name__,
        "has_predict": hasattr(model, "predict"),
        "has_predict_proba": hasattr(model, "predict_proba"),
    }

    # Récupérer le nombre de features
    if hasattr(model, "n_features_in_"):
        info["n_features"] = model.n_features_in_
    elif hasattr(model, "feature_names_in_"):
        info["n_features"] = len(model.feature_names_in_)
    else:
        # Fallback: essayer avec un exemple
        info["n_features"] = None

    # Récupérer les noms des features si disponibles
    if hasattr(model, "feature_names_in_"):
        info["feature_names"] = list(model.feature_names_in_)
    else:
        info["feature_names"] = None

    # Récupérer les classes si disponibles
    if hasattr(model, "classes_"):
        info["classes"] = list(model.classes_)
    else:
        info["classes"] = None

    return info


def extract_inference_pipeline(model):
    """
    Extrait la partie du pipeline pertinente pour l'inférence.

    SMOTE et autres techniques de sur-échantillonnage ne sont utilisées
    qu'à l'entraînement, pas à l'inférence. On les retire du pipeline.

    Args:
        model: Le modèle (peut être un Pipeline ou un modèle simple)

    Returns:
        Le modèle d'inférence (sans SMOTE)
    """
    from sklearn.pipeline import Pipeline

    # Si ce n'est pas un Pipeline, retourner tel quel
    if not isinstance(model, Pipeline):
        return model

    # Identifier les étapes à garder (pas SMOTE)
    inference_steps = []
    smote_removed = False

    for name, step in model.steps:
        step_type = type(step).__name__
        # Exclure SMOTE et autres techniques de sur-échantillonnage
        if 'SMOTE' in step_type or 'Sampler' in step_type:
            print(f"⚠️  Étape '{name}' ({step_type}) retirée "
                  "(sur-échantillonnage uniquement pour l'entraînement)")
            smote_removed = True
            continue
        inference_steps.append((name, step))

    # Si des étapes ont été retirées, créer un nouveau pipeline
    if smote_removed:
        if len(inference_steps) == 1:
            # Si une seule étape reste, retourner le modèle directement
            print(f"   → Pipeline simplifié en: {inference_steps[0][1]}")
            return inference_steps[0][1]
        else:
            # Créer un nouveau pipeline
            new_pipeline = Pipeline(inference_steps)
            print(f"   → Nouveau pipeline: "
                  f"{' → '.join([name for name, _ in inference_steps])}")
            return new_pipeline

    return model


def convert_to_onnx(
    model,
    n_features: int,
    output_path: str,
    target_opset: int = 12
) -> None:
    """
    Convertit le modèle scikit-learn en ONNX.

    Args:
        model: Le modèle scikit-learn à convertir
        n_features: Nombre de features d'entrée
        output_path: Chemin de sortie pour le fichier ONNX
        target_opset: Version de l'opset ONNX (défaut: 12)

    Raises:
        Exception: Si la conversion échoue
    """
    print("\n🔄 Conversion du modèle en ONNX...")
    print(f"   - Nombre de features: {n_features}")
    print(f"   - Target opset: {target_opset}")

    # Extraire le pipeline d'inférence (sans SMOTE)
    inference_model = extract_inference_pipeline(model)

    # Définir le type d'entrée (tableau de floats)
    initial_type = [("float_input", FloatTensorType([None, n_features]))]

    # Convertir le modèle
    try:
        onnx_model = convert_sklearn(
            inference_model,
            initial_types=initial_type,
            target_opset={'': target_opset, 'ai.onnx.ml': 3},
            options={
                "zipmap": False  # Désactiver zipmap pour predict_proba
            }
        )

        # Sauvegarder le modèle ONNX
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "wb") as f:
            f.write(onnx_model.SerializeToString())

        print(f"✅ Modèle ONNX sauvegardé: {output_path}")

        # Afficher la taille du fichier
        file_size = output_file.stat().st_size
        print(f"   - Taille: {file_size / 1024:.2f} KB")

    except Exception as e:
        print(f"❌ Erreur lors de la conversion: {e}")
        raise


def validate_onnx_model(
    original_model,
    onnx_path: str,
    n_features: int,
    n_samples: int = 10
) -> bool:
    """
    Valide le modèle ONNX en comparant avec le modèle original.

    Args:
        original_model: Le modèle scikit-learn original
        onnx_path: Chemin vers le modèle ONNX
        n_features: Nombre de features
        n_samples: Nombre d'échantillons de test

    Returns:
        True si la validation réussit, False sinon
    """
    print("\n🧪 Validation du modèle ONNX...")

    try:
        import onnxruntime as rt

        # Charger le modèle ONNX
        sess = rt.InferenceSession(onnx_path)

        # Générer des données de test aléatoires
        X_test = np.random.rand(n_samples, n_features).astype(np.float32)

        # Prédictions avec le modèle original
        y_sklearn = original_model.predict(X_test)

        # Prédictions avec le modèle ONNX
        input_name = sess.get_inputs()[0].name
        output_name = sess.get_outputs()[0].name
        y_onnx = sess.run([output_name], {input_name: X_test})[0]

        # Comparer les résultats
        differences = np.abs(y_sklearn - y_onnx.flatten())
        max_diff = np.max(differences)
        mean_diff = np.mean(differences)

        print(f"   - Échantillons testés: {n_samples}")
        print(f"   - Différence maximale: {max_diff:.10f}")
        print(f"   - Différence moyenne: {mean_diff:.10f}")

        # Valider que les différences sont négligeables
        if max_diff < 1e-5:
            print("✅ Validation réussie: les prédictions sont identiques")
            return True
        else:
            print(f"⚠️  Différences détectées (max: {max_diff})")
            return False

    except ImportError:
        print("⚠️  onnxruntime non installé, validation ignorée")
        print("   Installez avec: pip install onnxruntime")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        return False


def create_conversion_report(
    input_path: str,
    output_path: str,
    model_info: dict,
    validation_success: Optional[bool] = None
) -> str:
    """
    Crée un rapport de conversion.

    Args:
        input_path: Chemin du modèle source
        output_path: Chemin du modèle ONNX
        model_info: Informations sur le modèle
        validation_success: Résultat de la validation

    Returns:
        Le rapport sous forme de string
    """
    report = []
    report.append("=" * 70)
    report.append("RAPPORT DE CONVERSION ONNX")
    report.append("=" * 70)
    report.append("")
    report.append(f"Modèle source:  {input_path}")
    report.append(f"Modèle ONNX:    {output_path}")
    report.append("")
    report.append("Informations du modèle:")
    report.append(f"  - Type:       {model_info['type']}")
    report.append(f"  - Features:   {model_info['n_features']}")

    if model_info["feature_names"]:
        report.append(f"  - Noms:       {len(model_info['feature_names'])} "
                      "features nommées")

    if model_info["classes"]:
        report.append(f"  - Classes:    {model_info['classes']}")

    report.append("")
    report.append("Méthodes disponibles:")
    predict_icon = '✅' if model_info['has_predict'] else '❌'
    report.append(f"  - predict:        {predict_icon}")
    predict_proba_icon = '✅' if model_info['has_predict_proba'] else '❌'
    report.append(f"  - predict_proba:  {predict_proba_icon}")

    if validation_success is not None:
        report.append("")
        report.append("Validation:")
        validation_icon = '✅ Réussie' if validation_success else '❌ Échec'
        report.append(f"  - Statut:     {validation_icon}")

    report.append("")
    report.append("Prochaines étapes:")
    report.append("  1. Vérifier que le modèle ONNX fonctionne correctement")
    report.append("  2. Mettre à jour l'API pour utiliser onnxruntime")
    report.append("  3. Mettre à jour les tests unitaires")
    report.append("  4. Déployer la nouvelle version")
    report.append("")
    report.append("Documentation:")
    report.append("  - ONNX Runtime: https://onnxruntime.ai/")
    report.append("  - skl2onnx: https://onnx.ai/sklearn-onnx/")
    report.append("=" * 70)

    return "\n".join(report)


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description="Convertit un modèle scikit-learn en ONNX",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--input",
        "-i",
        default="model/model.pkl",
        help="Chemin du modèle pickle (défaut: model/model.pkl)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="model/model.onnx",
        help="Chemin de sortie ONNX (défaut: model/model.onnx)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Valider le modèle ONNX après conversion"
    )
    parser.add_argument(
        "--n-features",
        type=int,
        default=28,
        help="Nombre de features (défaut: 28)"
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=12,
        help="Version de l'opset ONNX (défaut: 12)"
    )

    args = parser.parse_args()

    try:
        # Charger le modèle
        model = load_pickle_model(args.input)

        # Récupérer les informations du modèle
        model_info = get_model_info(model)

        # Utiliser le nombre de features du modèle si disponible
        n_features = model_info["n_features"] or args.n_features
        print(f"   - Features: {n_features}")

        # Convertir en ONNX
        convert_to_onnx(
            model,
            n_features=n_features,
            output_path=args.output,
            target_opset=args.opset
        )

        # Valider si demandé
        validation_success = None
        if args.validate:
            validation_success = validate_onnx_model(
                model,
                args.output,
                n_features
            )

        # Créer et afficher le rapport
        report = create_conversion_report(
            args.input,
            args.output,
            model_info,
            validation_success
        )
        print("\n" + report)

        # Code de sortie
        if validation_success is False:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Erreur: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

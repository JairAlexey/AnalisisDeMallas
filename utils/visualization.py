"""
Utilidades para visualización de datos y resultados
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional, Union

def create_similarity_heatmap(similarity_matrix: np.ndarray, 
                             labels: List[str] = None, 
                             title: str = "Matriz de Similitud",
                             cmap: str = "viridis") -> plt.Figure:
    """
    Crea un mapa de calor para visualizar similitudes entre elementos
    
    Args:
        similarity_matrix: Matriz cuadrada de similitudes
        labels: Etiquetas para los ejes (opcional)
        title: Título del gráfico
        cmap: Mapa de colores a utilizar
        
    Returns:
        Objeto Figure de matplotlib
    """
    # Configurar figura
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Crear heatmap
    sns.heatmap(similarity_matrix, 
                annot=True, 
                cmap=cmap, 
                square=True,
                linewidths=.5,
                xticklabels=labels,
                yticklabels=labels,
                ax=ax)
    
    # Configurar título y etiquetas
    plt.title(title, fontsize=14)
    plt.tight_layout()
    
    return fig

def create_cluster_visualization(embeddings: np.ndarray, 
                                labels: List[int], 
                                names: List[str] = None,
                                title: str = "Visualización de Clusters") -> plt.Figure:
    """
    Crea una visualización 2D de clusters usando PCA
    
    Args:
        embeddings: Matriz de embeddings
        labels: Etiquetas de clusters
        names: Nombres de los elementos (opcional)
        title: Título del gráfico
        
    Returns:
        Objeto Figure de matplotlib
    """
    from sklearn.decomposition import PCA
    
    # Reducir dimensionalidad a 2D para visualización
    pca = PCA(n_components=2)
    reduced = pca.fit_transform(embeddings)
    
    # Configurar figura
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Crear scatter plot por cluster
    unique_labels = sorted(set(labels))
    colors = plt.cm.rainbow(np.linspace(0, 1, len(unique_labels)))
    
    for i, cluster_id in enumerate(unique_labels):
        cluster_points = reduced[labels == cluster_id]
        ax.scatter(cluster_points[:, 0], cluster_points[:, 1], 
                  color=colors[i], label=f'Cluster {cluster_id}',
                  alpha=0.7, s=80)
    
    # Añadir etiquetas si se proporcionan
    if names:
        for i, name in enumerate(names):
            ax.annotate(name, (reduced[i, 0], reduced[i, 1]), 
                       fontsize=8, alpha=0.7)
    
    # Configurar título y leyenda
    plt.title(title, fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    return fig

def format_curriculum_display(curriculum: Dict[str, List], 
                             highlight_subjects: List[str] = None) -> None:
    """
    Formatea y muestra una malla curricular en Streamlit
    
    Args:
        curriculum: Diccionario con semestres como claves y listas de materias como valores
        highlight_subjects: Lista de materias a resaltar (opcional)
    """
    if not curriculum:
        st.warning("No hay datos de malla curricular para mostrar")
        return
    
    # Crear pestañas para cada semestre
    tabs = st.tabs([f"Semestre {sem}" for sem in sorted(curriculum.keys(), key=lambda x: int(x))])
    
    # Determinar si se deben resaltar materias
    should_highlight = highlight_subjects is not None and len(highlight_subjects) > 0
    
    # Mostrar materias por semestre
    for i, semestre in enumerate(sorted(curriculum.keys(), key=lambda x: int(x))):
        materias = curriculum[semestre]
        
        with tabs[i]:
            for materia in materias:
                if isinstance(materia, dict) and "nombre" in materia:
                    # Formato para materias con detalles
                    nombre = materia["nombre"]
                    if should_highlight and nombre in highlight_subjects:
                        st.markdown(f"- 🌟 **{nombre}**")
                    else:
                        st.write(f"- {nombre}")
                elif isinstance(materia, str):
                    # Formato para materias que son solo strings
                    if should_highlight and materia in highlight_subjects:
                        st.markdown(f"- 🌟 **{materia}**")
                    else:
                        st.write(f"- {materia}")

def create_stacked_bar_chart(data: Dict[str, Dict[str, int]], 
                            title: str = "Distribución de Materias por Área") -> plt.Figure:
    """
    Crea un gráfico de barras apiladas para visualizar distribución
    
    Args:
        data: Diccionario anidado con datos para graficar
        title: Título del gráfico
        
    Returns:
        Objeto Figure de matplotlib
    """
    # Convertir a DataFrame
    df = pd.DataFrame(data)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Crear gráfico de barras apiladas
    df.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
    
    # Configurar título y etiquetas
    plt.title(title, fontsize=14)
    plt.xlabel('Categoría')
    plt.ylabel('Cantidad')
    plt.legend(title='Subcategoría', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    return fig

def create_comparison_radar_chart(data: Dict[str, List[float]], 
                                categories: List[str],
                                title: str = "Comparación de Perfiles") -> plt.Figure:
    """
    Crea un gráfico de radar para comparar perfiles
    
    Args:
        data: Diccionario con nombres como claves y listas de valores como valores
        categories: Lista de nombres de categorías
        title: Título del gráfico
        
    Returns:
        Objeto Figure de matplotlib
    """
    # Número de categorías
    N = len(categories)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Ángulos para el gráfico de radar
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Cerrar el círculo
    
    # Añadir categorías como etiquetas
    plt.xticks(angles[:-1], categories)
    
    # Graficar cada perfil
    for name, values in data.items():
        values_with_closure = values + values[:1]  # Cerrar el polígono
        ax.plot(angles, values_with_closure, linewidth=2, label=name)
        ax.fill(angles, values_with_closure, alpha=0.25)
    
    # Configurar título y leyenda
    plt.title(title, fontsize=14)
    plt.legend(loc='upper right')
    
    return fig

def display_recommendation_summary(recommendations: Dict[str, Any]) -> None:
    """
    Muestra un resumen de recomendaciones en Streamlit
    
    Args:
        recommendations: Diccionario con información de recomendaciones
    """
    if not recommendations:
        st.warning("No hay recomendaciones para mostrar")
        return
    
    # Crear secciones para diferentes tipos de recomendaciones
    st.markdown("### Resumen de Recomendaciones")
    
    # Mostrar materias existentes
    if "materias_existentes" in recommendations:
        st.markdown("#### Materias Identificadas")
        existing = recommendations["materias_existentes"]
        
        if existing:
            for materia in sorted(existing):
                st.markdown(f"- ✅ {materia}")
        else:
            st.info("No se identificaron materias existentes")
    
    # Mostrar materias recomendadas
    if "materias_a_agregar" in recommendations:
        st.markdown("#### Materias Recomendadas")
        to_add = recommendations["materias_a_agregar"]
        
        if to_add:
            for materia in sorted(to_add):
                st.markdown(f"- ⭐ {materia}")
        else:
            st.success("No se requiere agregar materias adicionales")
    
    # Mostrar métricas si existen
    if "metricas" in recommendations:
        metrics = recommendations["metricas"]
        cols = st.columns(len(metrics))
        
        for i, (key, value) in enumerate(metrics.items()):
            with cols[i]:
                st.metric(label=key, value=value)

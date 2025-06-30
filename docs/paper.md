---
title: "Data-to-Science (D2S): An open-source ecosystem for collaborative geospatial data science research"

tags:
  - Geospatial data management
  - Uncrewed Aerial System
  - Python
  - TypeScript

authors:
  - name: Minyoung Jung
    affiliation: '1'
    orcid: https://orcid.org/0000-0002-6419-5236
  - name: Benjamin G. Hancock
    affiliation: '1'
    orcid: https://orcid.org/0009-0005-9457-3479
  - name: Zhenyu C. Qian
    affiliation: '2'
    orcid: https://orcid.org/0000-0002-7310-8608
  - name: Na Zhuo
    affiliation: '2'
  - name: Ziqian Gong
    affiliation: '2'
  - name: Jarrod S. Doucette
    affiliation: '3'
    orcid: https://orcid.org/0000-0003-4027-2417
  - name: Jinha Jung
    affiliation: '1'
    corresponding: true
    email: jinha@purdue.edu
    orcid: https://orcid.org/0000-0003-1176-3540

affiliations:
  - index: 1
    name: Lyles School of Civil and Construction Engineering, Purdue University
  - index: 2
    name: Rueff School of Design, Art, and Performance, Purdue University
  - index: 3
    name: College of Agriculture Research Services, Purdue University

date: 10 June 2025
bibliography: paper.bib
---

# Summary

Recently, geospatial data has begun to be used across a wide range of research fields; however, its large size and unstructured nature present challenges in fostering cohesive collaboration among diverse disciplines. The **Data-to-Science (D2S)** ecosystem is an open-source platform that offers an easy-to-use web application and additional client applications, specifically designed for managing comprehensive geospatial data and thereby supporting a broad range of research applications. The D2S web application serves as the primary interface of the D2S ecosystem, originally intended for archiving and visualizing geospatial data, particularly uncrewed aerial system (UAS) data, which often poses management challenges for individual researchers. To assist those who wish to comprehensively analyze both archived data within the D2S and other external geospatial datasets, the current D2S ecosystem also includes three additional components: the [D2S Python module (*d2spy*)](https://py.d2s.org), the [QGIS plugin (*D2S Browser*)](https://plugins.qgis.org/plugins/d2s_browser/), and a [public STAC catalog](https://stac.d2s.org/) accessible via both API and browser interface.


# Statement of Need

With advances in sensor technologies and the growing emphasis on open science, the use of geospatial data is rapidly expanding across various research fields [@breunig2020geospatial]. Publicly available geospatial datasets, such as Landsat and Sentinel satellite data, are generally well-managed and distributed by their respective agencies. However, managing UAS-based geospatial data collected by individuals presents significant challenges because these data are often unstructured and large in size. Despite growing evidence for the usefulness of geospatial data in enabling multi-disciplinary research [@mohd2018remote; @duarte2022recent; @ecke2022uav; @molina2023review], the size and complexity of such data often hinder smooth collaborative research. As a result, there is a pressing need for infrastructure that simplifies the management of UAS-based geospatial data collected by individuals or small research groups. To address this need, D2S was developed as a web-based geospatial data management system designed to make handling and sharing such data more efficient and accessible.


# Data-to-Science Features

D2S uses a Python backend with a REST API built on open standards, connecting client applications to a PostgreSQL database with PostGIS for managing core application data and references to user-contributed datasets stored on the local file system. Full documentation on the system architecture is available in the GitHub README. 
The D2S frontend web application provides researchers with an intuitive interface, developed in collaboration with a dedicated UI/UX team and informed by user interviews. The design efforts focused on creating an intuitive interface tailored for geospatial researchers, enabling side-by-side view comparisons and supporting analytic workflows through user-centered navigation and clarity of visual feedback. Built around this tailored interface, the current D2S web application (v1.0) offers five core categories of functionality, as outlined in the table below: 

+--------------------+-----------------------------------------------------------+------------------------------------------------------------------+
| Category           | Description                                               | Functionalities                                                  |
+====================+===========================================================+==================================================================+
| **Catalog**        | Dynamic spatiotemporal cataloging of geospatial data in a |
|                    | cloud-optimized format, enabling users to seamlessly      |
|                    | access, browse, and visualize datasets without            | 
|                    | downloading them                                          | - Sorting geospatial data by time and location: 2D raster data   |
|                    |                                                           |   (.tif), 3D point cloud data (.las, .laz), and vector data      |
|                    |                                                           |   (.geojson, .shp)                                               |
|                    |                                                           | - Raster and vector data visualization with symbology            |
|                    |                                                           |   configuration                                                  |
|                    |                                                           | - Swipe comparison of geospatial data products across time or    |
|                    |                                                           |   data type                                                      |
|                    |                                                           | - Visualizing 3D point cloud data                                |
|                    |                                                           | \vspace{1em}                                                     |
+--------------------+-----------------------------------------------------------+------------------------------------------------------------------+
| **Collaboration**  | Sharing data with others within the D2S web application   |
|                    | or by sending a sharable link                             | - Managing teams and members                                     | 
|                    |                                                           | - Creating accessible links and/or QR codes for shared data      |
|                    |                                                           | - Granting public access to data with no account or API key      |
|                    |                                                           |   required                                                       |
|                    |                                                           | \vspace{1em}                                                     |
+--------------------+-----------------------------------------------------------+------------------------------------------------------------------+
| **Preprocessing**  | Producing geospatial data products, such as dense point   |
|                    | clouds, Digital Surface Models (DSM), and orthorectified  |
|                    | images, from raw UAS data                                 | - Connecting to a photogrammetry pipeline based on open-source   |
|                    |                                                           |   [OpenDroneMap (ODM)](https://www.opendronemap.org/) via        |
|                    |                                                           |   ClusterODM                                                     |
|                    |                                                           | - User configurable settings for the ODM pipeline                |
|                    |                                                           | \vspace{1em}                                                     |
+--------------------+-----------------------------------------------------------+------------------------------------------------------------------+
| **Postprocessing** | Basic analysis of geospatial data products                | - Calculating vegetation indices (NDVI¹, ExG², VARI³) and        |
|                    |                                                           |   hillshade from raster data                                     |
|                    |                                                           | - Generating Digital Terrain Models (DTM) and Normalized         |
|                    |                                                           |   Difference Height Models (NDHM) from point cloud data          |
|                    |                                                           | - Zonal statistics based on vector data                          |
|                    |                                                           | \vspace{1em}                                                     |
+--------------------+-----------------------------------------------------------+------------------------------------------------------------------+
| **Publishing**     | Publicly publishing data to the D2S STAC catalog          | - Generating and pushing STAC catalogs of datasets to be         |
|                    |                                                           |   publicly published                                             |
|                    |                                                           | \vspace{1em}                                                     |
+--------------------+-----------------------------------------------------------+------------------------------------------------------------------+
¹ NDVI = Normalized Difference Vegetation Index  
² ExG = Excess Green Vegetation Index  
³ VARI = Visual Atmospherically Resistant Index  

Furthermore, the Python module, [*d2spy*](https://py.d2s.org), is available through PyPI (https://py.d2s.org/), and the QGIS plugin, [*D2S Browser*](https://plugins.qgis.org/plugins/d2s_browser/), is also available at https://plugins.qgis.org/plugins/d2s_browser/. Notably, with *d2spy*, researchers can comprehensively analyze the geospatial data stored within the D2S ecosystem as well as external public datasets, such as Landsat, by seamlessly integrating with other Python packages like *geemap* [@wu2020geemap] and *leafmap* [@wu2021leafmap]. Additionally, datasets, such as 3DEP and NAIP datasets, can also be incorporated into collective analyses as they are provided via the [D2S STAC catalog](https://stac.d2s.org/) (https://stac.d2s.org/) as part of the D2S ecosystem.


# Data-to-Science Tutorials

The D2S web application is containerized using Docker, enabling consistent deployment across both Linux servers using Docker Compose and cloud environments orchestrated with Kubernetes. A single Docker Compose file enables local deployment, while public Docker images and minimal configuration make the platform easy to integrate into cloud infrastructure. Step-by-step instructions are available in the GitHub README. The basic user manual for the D2S functionalities (as described in the table above) is available at https://docs.gdsl.org/data-to-science-user-manual with the publicly available sample data. A collection of example guides for using the D2S Python module, d2spy, is also available at https://py.d2s.org/guides/. In addition, a range of real-world application cases using the D2S ecosystem is provided as video tutorials at https://d2s.org/workshop.


# Acknowledgements
This work was partially supported by the Purdue Plant Science 2.0 Initiative, the Institute for Digital Forestry at Purdue, the PERSEUS grant (#2023-68012-38992) under USDA NIFA, the EFFICACI grant (#NR233A750004G044) under NCRS, and the National Agricultural Producers Data Cooperative (Award 2023-77039-41033; Sub-award 25-6231-0428-008) under USDA.


# References
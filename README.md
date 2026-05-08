# PreventDM

A population health decision support platform for diabetes prevention, designed for use by public health units, regional health authorities, and chronic disease prevention programs.

## Overview

PreventDM combines a validated machine learning risk model with established clinical risk scores to help public health units identify individuals at elevated risk of progressing from prediabetes to Type 2 Diabetes, target prevention resources efficiently, and monitor program outcomes at the population level.

The platform is built as a multi-service application with a Flutter cross-platform frontend, a Python FastAPI orchestration backend, a Rust validation and scoring service, a Python machine learning inference service, and a PostgreSQL data layer.

## Status

This project is currently under active development. The repository is being built incrementally, beginning with the backend services and the supporting infrastructure.

## Architecture

The system is organized into five tiers. Public health users including prevention coordinators, epidemiologists, and program managers interact with a Flutter cross-platform application. The Flutter frontend communicates with a Python FastAPI backend that handles authentication, business logic, and orchestration. The backend delegates data validation and parallel computation of established clinical risk scores to a Rust Axum service, and delegates custom risk prediction and SHAP-based interpretability to a Python machine learning service. PostgreSQL stores persistent data and Redis provides caching and session management.

Detailed architectural diagrams are available in the docs folder.

## Repository structure

The repository is organized as follows:

- backend contains the Python FastAPI orchestration service
- rust_service contains the Rust Axum validation and scoring service
- ml_service contains the Python machine learning inference service
- cli contains the command-line test harness
- docs contains architectural diagrams and supporting documentation

## License

This project is currently developed for educational and portfolio purposes. Licensing terms will be finalized prior to any production deployment.
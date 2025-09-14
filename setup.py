"""Setup configuration for Telematics Insurance Platform."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="telematics-insurance-ml",
    version="1.0.0",
    author="Telematics Developer",
    author_email="telematics.dev@example.com",
    description="Production-grade telematics platform for usage-based auto insurance with advanced ML risk scoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/[YourUsername]/telematics-insurance-ml",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business :: Financial :: Insurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
        ],
        "cloud": [
            "boto3>=1.26.0",
            "kubernetes>=24.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "telematics-demo=bin.quick_prototype:main",
            "telematics-train=bin.train_risk_models:main",
            "telematics-evaluate=bin.evaluate_models:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json", "*.html", "*.css", "*.js"],
    },
    project_urls={
        "Bug Reports": "https://github.com/[YourUsername]/telematics-insurance-ml/issues",
        "Source": "https://github.com/[YourUsername]/telematics-insurance-ml",
        "Live Demo": "http://telematics-alb-1568825282.us-east-2.elb.amazonaws.com",
        "Documentation": "https://github.com/[YourUsername]/telematics-insurance-ml/blob/main/docs/README.md",
    },
)

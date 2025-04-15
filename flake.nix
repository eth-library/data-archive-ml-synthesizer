{
  description = "Python development environment using Poetry and Nix";

  inputs = {
    # Using unstable is more likely to have newer Python versions like 3.14+
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # --- IMPORTANT ---
        # Specify the Python version provided by Nix.
        # This version MUST meet the minimum requirement specified in your
        # project's pyproject.toml file (e.g., python = ">=3.14").
        # Adjust pkgs.python312 below accordingly (e.g., pkgs.python313, pkgs.python312).
        pythonVersion = pkgs.python312;
        # --- IMPORTANT ---

        devPackages = [
          pythonVersion                             # Base Python interpreter
          pkgs.poetry                               # Poetry for dependency management
          pkgs.python312Packages.pytest             # Pytest available in the shell (if needed outside Poetry)
        ];

      in
      {
        devShells.default = pkgs.mkShell {
          packages = devPackages;

          shellHook = ''
            echo "Entering Nix development shell..."

            # Configure Poetry to create the virtual environment inside the project directory
            poetry config virtualenvs.in-project true --local || true

            # Check if pyproject.toml exists
            if [ -f pyproject.toml ]; then
              echo "Setting up Python virtual environment and installing dependencies with Poetry (including dev extras)..."
              # Install all dependencies including the optional dev dependencies
              poetry install --with dev

              # Automatically activate the virtual environment if it exists
              if [ -f .venv/bin/activate ]; then
                echo "Activating Poetry virtual environment..."
                source .venv/bin/activate

                # Add the current directory to PYTHONPATH, so your project modules are accessible
                export PYTHONPATH="$PYTHONPATH:$(pwd)"
                echo "Added $(pwd) to PYTHONPATH"
              else
                echo "Warning: .venv not found even after installation."
              fi

              echo ""
              echo "------------------------------------------------------------------------"
              echo "Nix/Poetry development environment ready!"
              echo ""
              echo "A '.venv' directory has been created/updated using Python ${pythonVersion.version} as base."
              echo "Your IDE should be configured to use the Python interpreter located at:"
              echo "  ./.venv/bin/python"
              echo ""
              echo "Run commands within the managed environment using:"
              echo "  poetry run <your_command>"
              echo "Or activate manually: source .venv/bin/activate"
              echo "------------------------------------------------------------------------"
            else
              echo "WARNING: 'pyproject.toml' not found. Skipping Poetry dependency installation."
            fi

            echo "--------------------------------------------------------------"
            echo "Activated reproducible dev environment for data-archive-ml-synthesizer"
            echo "System: ${system}"
            echo "Python interpreter: $(which python)"
            echo "Python version: $(python --version 2>&1)"
            echo "Dependency management is handled by Poetry."
            echo "--------------------------------------------------------------"

            # Clear SOURCE_DATE_EPOCH to avoid potential conflicts in reproducible builds
            unset SOURCE_DATE_EPOCH
          '';
        };
      }
    );
}

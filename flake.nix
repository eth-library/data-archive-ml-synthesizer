# flake.nix
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
        # Adjust pkgs.python314 below accordingly (e.g., pkgs.python313, pkgs.python312).
        pythonVersion = pkgs.python312;
        # --- IMPORTANT ---

        devPackages = [
          pythonVersion       # Provides the base Python interpreter
          pkgs.poetry         # Poetry for dependency management
          pkgs.python312Packages.pytest  # Pytest available in the shell
        ];

      in
      {
        devShells.default = pkgs.mkShell {
          packages = devPackages;

          shellHook = ''
            echo "Entering Nix development shell..."

            # Configure Poetry to create the virtual environment inside the project directory
            poetry config virtualenvs.in-project true --local || true

            # We removed 'poetry config virtualenvs.prefer-active-python true --local'
            # as it caused warnings with your Poetry version and is often the default behavior anyway.
            # Poetry will use the active Python (provided by Nix via 'pythonVersion' above)
            # to bootstrap the virtual environment.

            # Check if pyproject.toml exists
              if [ -f pyproject.toml ]; then
                echo "Setting up Python virtual environment and installing dependencies with Poetry..."
                poetry sync

                # Automatically activate the virtual environment
                if [ -f .venv/bin/activate ]; then
                  echo "Activating Poetry virtual environment..."
                  source .venv/bin/activate

                  # Add src directory to PYTHONPATH
                  export PYTHONPATH="$PYTHONPATH:$(pwd)"
                  echo "Added $(pwd) to PYTHONPATH"
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
              echo "Or activate manually: source ./.venv/bin/activate"
              echo "------------------------------------------------------------------------"
            else
              echo "WARNING: 'pyproject.toml' not found. Skipping 'poetry install'."
            fi

            echo "--------------------------------------------------------------"
            echo "Activated reproducible dev environment for data-archive-ml-synthesizer"
            echo "System: ${system}"
            echo "Python interpreter: $(which python)"
            echo "Python version: $(python --version 2>&1)"
            echo "Dependency management is handled by Poetry."
            echo "--------------------------------------------------------------"

            unset SOURCE_DATE_EPOCH
          '';
        };
      }
    );
}

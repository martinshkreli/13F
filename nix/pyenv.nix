# python-env.nix 
# this makes an inpure shell env where we can run python commands like we would on a normal FHS OS so we can import the requirements.txt and the packages should install 


with import <nixpkgs> { };

let
  pythonPackages = python3Packages;

  startPythonScript = ''
    # put the commands to start python script here
    # python main.py
    # python 13f.py $F
  '';

  cleanupVenvScript = '' 
    rm -rf .venv
    python -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

  '';
in pkgs.mkShell rec {
  name = "impurePythonEnv";
  venvDir = "./.venv";
  buildInputs = [
    # A Python interpreter including the 'venv' module is required to bootstrap
    # the environment.
    pythonPackages.python

    # This executes some shell code to initialize a venv in $venvDir before
    # dropping into the shell
    pythonPackages.venvShellHook

    # IF WE ARE GETTING ERRORS ABOUT NOT FINDING THE LIBRARY, WE CAN ADD THE LIBRARY HERE

    stdenv.cc.cc.lib # needed this to import yfinance; it was giving me issues about not finding cstdlib++
    # ImportError: libstdc++.so.6: cannot open shared object file: No such file or directory
  ];

  preShellHook = ''
     ${cleanupVenvScript}
  '';
  
  # Run this command, only after creating the virtual environment
  postVenvCreation = ''
    unset SOURCE_DATE_EPOCH
    export LD_LIBRARY_PATH=${stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH # see default.nix
    
    # install after cleanup
    pip install -r requirements.txt

  '';

  # Now we can execute any commands within the virtual environment.
  postShellHook = ''
    # allow pip to install wheels
    unset SOURCE_DATE_EPOCH
    export LD_LIBRARY_PATH=${stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH # see default.nix
  '';
}

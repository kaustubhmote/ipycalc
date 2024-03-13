# ipycalc

ipycalc (ipython calculator) is a quick way to start an ipython console in a kitty terminal window.




It does the following things:

- Loads in modules that you regularly use in the background in a separate non-blocking thread so that you can start typing without having to wait for all modules to load
- Allows plotting (using matplotlib)
- Unit conversion using the `pint` library
- Uncertainty calculations using the `uncertainties` library
- Gives a convenient way to incorporate your own functions that are preloaded


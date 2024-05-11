# ipycalc

`ipycalc` (IPython Calculator) is a quick way to start an IPython console in a kitty terminal window. Its main feature is that it loads in modules that you regularly use in the background in a separate non-blocking thread so that you can start typing without having to wait for all modules to load. Here is how it should look when set up:

![Demo](ipycalc.mp4)



It also does the following things:

- Allows quick plotting in the terminal (using `matplotlib` and `matplotlib-kitty-backend`)
- Unit conversion using the `pint` library.
- Uncertainty calculations using the `uncertainties` library.
- Ability to use datetime using the `pendulum` library
- Some basic financial functions (compound interest, sip, etc)
- Gives a convenient way to incorporate your own functions that are also preloaded.


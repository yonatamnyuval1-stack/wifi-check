# WiFi check

A small terminal program that looks at nearby WiFi networks and rates them.

It uses the network list Windows already shows. It does not connect to any network.

## Run

WiFi has to be on. Then, from this folder:

The program scans 3 times, with a short wait between scans, so it takes a few seconds.

## What you see

Networks are printed from the lowest final score to the highest.

security score: encryption, and if the same name shows up with two different security types
stability score: signal, jumps, channel and band
score: the lower of those two

For a name with several access points, the strongest signal is kept. The signal used for the score is the middle of the 3 scans.

## License

MIT

## author

Jonathan Jacob
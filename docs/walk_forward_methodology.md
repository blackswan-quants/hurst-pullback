Perform the WFA with a rolling window of 2/3 years for the optimization. Then test the optimized strategy on a test window of 6 months. The ratio test/opt is suggested around 25% - 35%. Doing this we are able to test stability and robustness, and also test the strategy on out of sample data.

Then we'll have to compute strategy metrics and compare OOS metrics with the IS ones. The relative performance on the OOS data will tell us if our strategy is supposed to perform well in real time trading. This is the easiest way to test this.

Also the re-optimization frequency depends on the choice of the opt/test window. It is suggested to take it equal to the test one. For example, if we optimize our strategy on a 2 years window and test it on a 6 months one, it will be a good practice to re-optimize it after 6 months.

Then we could also run MC simulation to sample new scenarios on which we could test again our strategy to test again robustness. This could be done also on the parameters.
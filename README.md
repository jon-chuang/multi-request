# MultiRequests

A system for fast and robust anonymised parallel requests over a shared pool of unreliable proxies to a potentially unfriendly peer. 

![Images/DiagramSharp.png](https://github.com/raskellr/test/blob/master/images/DiagramSharp.png)

Although not suggested use case, potentially a tool for carrying out spamming, scraping, and captcha avoidance without a botnet or paid proxies.

## Problem Specification
One of our objectives was to have as many requests running concurrently as possible. We do so using multiprocessing.

In a test case, this optimum number was about 300, beyond which performance started to decline due to detection. Running on an laptop, our system was able to perform about 105,000 http get requests over 45 minutes to a single website with captcha and behavioural-detection capabilities, all while performing on-the-fly data munging. On average, 80% of those requests were successful (roughly 30 successful requests/second).
 
Room for improvement: In the beginning, computation was a much smaller time-factor compared to request latency, especially through mediating proxy. (IO bound) Hence little or no attention was paid to computationally performant implementation. However, scaling up to 500 concurrent requests, access to the proxy pool for read and writes started locking out.

### Solution
Achieves performance by carrying out scoring and blacklisting of proxies, and evades detection by rotating data and proxies. As the system operates on a one job one proxy basis to keep a low network profile on each proxy, proxies are locked out when in use. However, for large jobs with several hundreds of concurrent requests, one often encounters a proxy bottleneck when fetching from free, regularly updated sources on the internet.

To solve this problem, we also a feature called virtualisation, where the proxy supply can be increased arbitrarily by creating copies of proxies already in use. When any of the copies are returned to the pool, the copy with the highest-level of virtualisation is destroyed. This way, as more real proxies enter the pool, all the virtual proxies will eventually be destroyed. 

However, the higher-level of virtualisation, the greater the amount of concurrent score adjustment of single proxies. This could lead to shorter lifespans for proxies that are not performing on a short-term basis.

### Prerequisites

(Optional) Install [hipsterplot](https://github.com/imh/hipsterplot)

Python3

### How to Use
The user must implement:
* The data classes for for the superclass Data, which must implement the following methods:

`__init__`, `__str__`, `next`

    As `__str__` will serve as a unique identifier, please try to make the name unique. (Note to self: change to use `__repr__` instead.)

* The batch_handler instance which initiates and runs the MultiBatchHandler session, and pipes around data. 
* The call function to a particular webservice, which returns signals (success, score, completed, switch) to the batch handler for scoring proxies and rotating data and proxies. 
* Tuned settings for the various handlers, such as optimal number of proxies in pool, number of batch_handler processes, amount of staggering to initial batches to avoid network spike detection, timeout parameters for the http request tests and the deployment environment calls, thresholds for proxy blacklisting and proxy and data switching. 

### How to Configure the settings.py File
To be continued


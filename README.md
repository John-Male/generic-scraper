# generic-scraper

A configuration-driven web scraper. Describe a site in a spec file; get
structured records out. Built by a SwarmForge six-pack running on Claude Code.

A quick test to see how SwarmForge works to create a generic scraper. The Sonnet 5 model was used for all of the steps. The feature gerkhin files were created from a very brief voice conversation using SuperWhisper. The first 4 phases in the 6 step process ran in less than 2 hours. The hardener process ran for about 1.5 hours and the QA section ran for about 20 minutes. The process runs many local jobs that do not consume tokens.  

Next I will be going to run a similar test using the four-pack with the same model to compare the differences in the outcomes

I am quite impressed with the quality of the code that has been generated so far, I have not attempted to use the code yet

## actual text used to create feature gerkhins in copilot using Think Deeper
```
create gerkin scripts to describe a python generic scraper that will be able to use number of different scraping techniques the main class for the Scraper will be able to receive


ScraperType class
initScraper class consists of variables:
- Scraper type, which can be the defaults
- Requests
- Playwright
- Selenium
- Browser type
- Default none
- Secondary choices
- Chrome

Firefox, then proxy, proxy information, pass key for that header data, create processing type. Values can be like beautiful soup, common requests.
```
## claude session comments on using Sonnet 5
Sonnet 5 is the default model for my cli login

```
That's the more interesting option than switching all six: the roles have genuinely different demands. The specifier writes the spec everything downstream depends on, and the architect and hardender do the reasoning-heavy review — those are where a stronger model pays. The coder implementing a named scenario and the cleaner removing duplication are well within Sonnet's range, and they're also the highest-volume roles, so leaving them on Sonnet keeps the usage burn down.

Worth weighing against the fact that six concurrent sessions already consume quota fast; putting all six on Opus would multiply that. Restart the swarm after editing the config — the launch command is built at startup.
```

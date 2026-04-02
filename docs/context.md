In this project you will design a end-to-end ML project that leverages the following concepts/technologies:
- multimodal data
- embddings and vector db
- point-in-time correctness
- online and offline feature store using feast and redis
- kafka and spark streaming
- spark and hive for offline feature store
- hdfs if necessary
- serving & monitoring (prediction drift, features drift, system metrics, ....)
- neural net architecture (ideally transformers)
- a rich set of features from diffrerent data sources
- model training (with experiment tracking and model regsitry)
- job orchestration


I will let you choose the project and theme. Make sure to choose something that will allow you to cover all the above thematics.

Concerning the dataset, you can generate a mock dataset or download something from the internet. You may need to fake the real time aspect by creating a service that will act as a data source or something else.

Create a docker-compose that will contain all the necessary services. this is done for quick dev.
backend should not be in docker-compose, same for frontend which should use vite. This will enable quick dev.
when all is done we should have infra-as-code and gitops to deploy easily in prod.

Once you are done, the project should be complete. Do not fake services, this project should be production grade.

You should use mlops best practices and document the architecture as if you were presenting a system design interview for ml infra focused.
Document the information in @docs/sys-design.md
You will need to document:
- business context
- business objective
- non functional requirements
- high level objective
- datasets and features
- model deep dive (architecture, loss funciton and reason why you chose it)
- metrics (offline and online)
- deployment (serving/monitoing/retraining)
- infrastructure ascii architecture (give a high level then show each layer by itself)
- infra deep dive
- stack used
Justify all your choices and explain the tradeoffs

Inspire yourself by using the following article:
- https://jeftaylo.medium.com/from-devops-to-mlops-why-employers-care-and-how-i-built-a-fortune-500-stack-in-my-spare-bedroom-ce0d06dd3c61

The goal of this project is to learn ml sys design (infra focused) at a production level.
You will need to:
- imagine or use a dataset
- use real time features
- use docker-compose (we will not deploy, but ideally the architecture should be similar to a prod ready project)
- document the concepts in @docs/concepts.md
- give some teachings in @docs/lessons.md
- keep track of your progress @docs/progress.md (everytime you start or end a task, you will log it there, this document should have a header introducing it)
- log your architectural decisions  @docs/architectural-decisions.md
- make sure to use caching, feature-store (feast), spark and vector db 




Methodology:
Lets first brainstorm and agree on the project idea. Once the objective is clear we will create a plan.

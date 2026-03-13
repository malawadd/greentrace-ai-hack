# Passing input to Actor

Copy for LLM

The efficient way to run an Actor and retrieve results is by passing input data directly to the `call` method. This method allows you to configure the Actor's input, execute it, and either get a reference to the running Actor or wait for its completion.

The following example demonstrates how to pass input to the `apify/instagram-hashtag-scraper` Actor and wait for it to finish.

* Async client
* Sync client

```
import asyncio
from datetime import timedelta

from apify_client import ApifyClientAsync

TOKEN = 'MY-APIFY-TOKEN'


async def main() -> None:
    # Client initialization with the API token
    apify_client = ApifyClientAsync(token=TOKEN)

    # Get the Actor client
    actor_client = apify_client.actor('apify/instagram-hashtag-scraper')

    input_data = {'hashtags': ['rainbow'], 'resultsLimit': 20}

    # Run the Actor and wait for it to finish up to 60 seconds.
    # Input is not persisted for next runs.
    run_result = await actor_client.call(
        run_input=input_data, timeout=timedelta(seconds=60)
    )


if __name__ == '__main__':
    asyncio.run(main())
```

```
from datetime import timedelta

from apify_client import ApifyClient

TOKEN = 'MY-APIFY-TOKEN'


def main() -> None:
    # Client initialization with the API token
    apify_client = ApifyClient(token=TOKEN)

    # Get the Actor client
    actor_client = apify_client.actor('apify/instagram-hashtag-scraper')

    input_data = {'hashtags': ['rainbow'], 'resultsLimit': 20}

    # Run the Actor and wait for it to finish up to 60 seconds.
    # Input is not persisted for next runs.
    run_result = actor_client.call(run_input=input_data, timeout=timedelta(seconds=60))


if __name__ == '__main__':
    main()
```


# Manage tasks for reusable input

Copy for LLM

When you need to run multiple inputs with the same Actor, the most convenient approach is to create multiple [tasks](https://docs.apify.com/platform/actors/running/tasks), each with different input configurations. Task inputs are stored on the Apify platform when the task is created, allowing you to reuse them easily.

The following example demonstrates how to create tasks for the `apify/instagram-hashtag-scraper` Actor with different inputs, manage task clients, and execute them asynchronously:

* Async client
* Sync client

```
import asyncio

from apify_client import ApifyClientAsync

TOKEN = 'MY-APIFY-TOKEN'
HASHTAGS = ['zebra', 'lion', 'hippo']


async def main() -> None:
    apify_client = ApifyClientAsync(token=TOKEN)

    # Create Apify tasks
    apify_tasks = []
    apify_tasks_client = apify_client.tasks()

    for hashtag in HASHTAGS:
        apify_task = await apify_tasks_client.create(
            name=f'hashtags-{hashtag}',
            actor_id='apify/instagram-hashtag-scraper',
            task_input={'hashtags': [hashtag], 'resultsLimit': 20},
            memory_mbytes=1024,
        )
        apify_tasks.append(apify_task)

    print('Tasks created:', apify_tasks)

    # Create Apify task clients
    apify_task_clients = [apify_client.task(task.id) for task in apify_tasks]

    print('Task clients created:', apify_task_clients)

    # Execute Apify tasks
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(client.call()) for client in apify_task_clients]

    task_run_results = [task.result() for task in tasks]

    # Filter out None results (tasks that failed to return a run)
    successful_runs = [run for run in task_run_results if run is not None]

    print('Task results:', successful_runs)


if __name__ == '__main__':
    asyncio.run(main())
```

```
from apify_client import ApifyClient

TOKEN = 'MY-APIFY-TOKEN'
HASHTAGS = ['zebra', 'lion', 'hippo']


def main() -> None:
    apify_client = ApifyClient(token=TOKEN)

    # Create Apify tasks
    apify_tasks = []
    apify_tasks_client = apify_client.tasks()

    for hashtag in HASHTAGS:
        apify_task = apify_tasks_client.create(
            name=f'hashtags-{hashtag}',
            actor_id='apify/instagram-hashtag-scraper',
            task_input={'hashtags': [hashtag], 'resultsLimit': 20},
            memory_mbytes=1024,
        )
        apify_tasks.append(apify_task)

    print('Tasks created:', apify_tasks)

    # Create Apify task clients
    apify_task_clients = [apify_client.task(task.id) for task in apify_tasks]

    print('Task clients created:', apify_task_clients)

    # Execute Apify tasks
    task_run_results = [client.call() for client in apify_task_clients]

    # Filter out None results (tasks that failed to return a run)
    successful_runs = [run for run in task_run_results if run is not None]

    print('Task results:', successful_runs)


if __name__ == '__main__':
    main()
```


# Retrieve Actor data

Copy for LLM

Actor output data is stored in [datasets](https://docs.apify.com/platform/storage/dataset), which can be retrieved from individual Actor runs. Dataset items support pagination for efficient retrieval, and multiple datasets can be merged into a single dataset for further analysis. This merged dataset can then be exported into various formats such as CSV, JSON, XLSX, or XML. Additionally, [integrations](https://docs.apify.com/platform/integrations) provide powerful tools to automate data workflows.

The following example demonstrates how to fetch datasets from an Actor's runs, paginate through their items, and merge them into a single dataset for unified analysis:

* Async client
* Sync client

```
import asyncio

from apify_client import ApifyClientAsync

TOKEN = 'MY-APIFY-TOKEN'


async def main() -> None:
    # Client initialization with the API token
    apify_client = ApifyClientAsync(token=TOKEN)
    actor_client = apify_client.actor('apify/instagram-hashtag-scraper')
    runs_client = actor_client.runs()

    # See pagination to understand how to get more datasets
    actor_datasets = await runs_client.list(limit=20)

    datasets_client = apify_client.datasets()
    merging_dataset = await datasets_client.get_or_create(name='merge-dataset')

    for dataset_item in actor_datasets.items:
        # Dataset items can be handled here. Dataset items can be paginated
        dataset_client = apify_client.dataset(dataset_item.id)
        dataset_items = await dataset_client.list_items(limit=1000)

        # Items can be pushed to single dataset
        merging_dataset_client = apify_client.dataset(merging_dataset.id)
        await merging_dataset_client.push_items(dataset_items.items)

        # ...


if __name__ == '__main__':
    asyncio.run(main())
```

```
from apify_client import ApifyClient

TOKEN = 'MY-APIFY-TOKEN'


def main() -> None:
    # Client initialization with the API token
    apify_client = ApifyClient(token=TOKEN)
    actor_client = apify_client.actor('apify/instagram-hashtag-scraper')
    runs_client = actor_client.runs()

    # See pagination to understand how to get more datasets
    actor_datasets = runs_client.list(limit=20)

    datasets_client = apify_client.datasets()
    merging_dataset = datasets_client.get_or_create(name='merge-dataset')

    for dataset_item in actor_datasets.items:
        # Dataset items can be handled here. Dataset items can be paginated
        dataset_client = apify_client.dataset(dataset_item.id)
        dataset_items = dataset_client.list_items(limit=1000)

        # Items can be pushed to single dataset
        merging_dataset_client = apify_client.dataset(merging_dataset.id)
        merging_dataset_client.push_items(dataset_items.items)

        # ...


if __name__ == '__main__':
    main()
```
# Integration with data libraries

Copy for LLM

The Apify client for Python seamlessly integrates with data analysis libraries like [Pandas](https://pandas.pydata.org/). This allows you to load dataset items directly into a Pandas [DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html) for efficient manipulation and analysis. Pandas provides robust data structures and tools for handling large datasets, making it a powerful addition to your Apify workflows.

The following example demonstrates how to retrieve items from the most recent dataset of an Actor run and load them into a Pandas DataFrame for further analysis:

* Async client
* Sync client

```
import asyncio

import pandas as pd

from apify_client import ApifyClientAsync

TOKEN = 'MY-APIFY-TOKEN'


async def main() -> None:
    # Initialize the Apify client
    apify_client = ApifyClientAsync(token=TOKEN)
    actor_client = apify_client.actor('apify/web-scraper')
    run_client = actor_client.last_run()
    dataset_client = run_client.dataset()

    # Load items from last dataset run
    dataset_data = await dataset_client.list_items()

    # Pass dataset items to Pandas DataFrame
    data_frame = pd.DataFrame(dataset_data.items)

    print(data_frame.info)


if __name__ == '__main__':
    asyncio.run(main())
```

```
import pandas as pd

from apify_client import ApifyClient

TOKEN = 'MY-APIFY-TOKEN'


def main() -> None:
    # Initialize the Apify client
    apify_client = ApifyClient(token=TOKEN)
    actor_client = apify_client.actor('apify/web-scraper')
    run_client = actor_client.last_run()
    dataset_client = run_client.dataset()

    # Load items from last dataset run
    dataset_data = dataset_client.list_items()

    # Pass dataset items to Pandas DataFrame
    data_frame = pd.DataFrame(dataset_data.items)

    print(data_frame.info)


if __name__ == '__main__':
    main()
```

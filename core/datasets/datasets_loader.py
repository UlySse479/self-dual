# Modified based on: https://github.com/microsoft/ProphetNet/blob/master/CRITIC/src/datasets/dataset_loader.py
import os
from typing import Any, Dict, Union

import datasets
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict

from core.utils.utils import extract_boxed_from_str
DIR = os.path.join(os.path.dirname(__file__))


class DatasetLoader(object):
    """Dataset loader class."""

    # Datasets implemented in this repo
    # Either they do not exist in the datasets library or they have something improper
    own_dataset = {}
    own_jsonl_datset = {
        # MATH dataset is downloaded from https://github.com/microsoft/ToRA/blob/main/src/data/math/train.jsonl
        "math":{
            "test": os.path.join(DIR, "math/test.jsonl"),
            "train": os.path.join(DIR, "math/train.jsonl"),
        }
    }

    @staticmethod
    def load_dataset(
        dataset_name: str,
        split: str = None,
        name: str = None,
        dataset_key_map: Dict[str, str] = None,
        **kwargs: Any
    ) -> Union[DatasetDict, Dataset, IterableDatasetDict, IterableDataset]:
        """
        Load dataset from the datasets library or from this repo.
        Args:
            dataset_name: name of the dataset
            split: split of the dataset
            dataset_subset_name: subset name of the dataset
            dataset_key_map: mapping original keys to a unified set of keys
            **kwargs: arguments to pass to the dataset

        Returns: dataset

        """
        # Check whether the dataset is in the own_dataset dictionary
        if dataset_name in DatasetLoader.own_dataset.keys():
            dataset_path = DatasetLoader.own_dataset[dataset_name]
            dataset = datasets.load_dataset(
                path=dataset_path,
                split=split,
                name=name,
                **kwargs
            )
        elif dataset_name in DatasetLoader.own_jsonl_datset.keys():
            datafiles = DatasetLoader.own_jsonl_datset[dataset_name]
            dataset = datasets.load_dataset(
                path='json',
                data_files=datafiles,
                split=split,
                name=name,
                **kwargs
            )
        else:
            # Load from the datasets library
            dataset = datasets.load_dataset(
                path=dataset_name,
                split=split,
                name=name,
                **kwargs
            )

        if dataset_key_map:
            reverse_dataset_key_map = {v: k for k, v in dataset_key_map.items()}
            dataset = dataset.rename_columns(reverse_dataset_key_map)

        return dataset

def load_format_test_datasets(dataset_name:str="gsm8k", split:str="test") -> Dataset:
    """Load Format test dataset"""
    dataset_loader = DatasetLoader()
    dataset = None
    
    if dataset_name == "gsm8k":
        dataset = dataset_loader.load_dataset(
            dataset_name='gsm8k',
            split=split,
            name='main',
            dataset_key_map=
                {
                    "solution": "answer" # Change the 'answer' key to 'solution'
                }

        )
        def add_answer_column(example: Dict[str, Any]) -> Dict[str, Any]:
            # Add answer column to the dataset
            example["answer"] = example["solution"].split("####")[-1].strip()
            return example
        dataset = dataset.map(
            add_answer_column,
            desc="Add answer column to the dataset"
        )
    elif dataset_name == "svamp":
        dataset = dataset_loader.load_dataset(
            dataset_name='ChilleD/SVAMP',
            split=split,
            dataset_key_map=
                {
                    "question": "question_concat",
                    "answer": "Answer"
                }
        )
    elif dataset_name == "math":
        # MATH dataset is not available in the datasets library!
        try:
            dataset = dataset_loader.load_dataset(
                dataset_name='competition_math',
                split=split,
                dataset_key_map=
                    {
                        "problem": "question",
                    }
            )
        except Exception as e:
            print(f"Error loading dataset from datasets library: {e}")
            # If loading from the datasets library fails, load from the local jsonl file
            dataset = dataset_loader.load_dataset(
                dataset_name='math',
                split=split,
                dataset_key_map=
                    {
                        "question": "problem",
                    }
            )
        finally:
            # Add answer column to the dataset
            def add_answer_column(example: Dict[str, Any]) -> Dict[str, Any]:
                # Add answer column to the dataset
                example["answer"] = extract_boxed_from_str(example["solution"])
                return example
            # Use map to apply the function to each example in the dataset
            dataset = dataset.map(
                add_answer_column,
                desc="Add answer column to the dataset"
            )
    elif dataset_name == "aime":
        dataset_sub1 = dataset_loader.load_dataset(
            dataset_name='opencompass/AIME2025',
            name='AIME2025-I',
            split='test',
        )
        dataset_sub2 = dataset_loader.load_dataset(
            dataset_name='opencompass/AIME2025',
            name='AIME2025-II',
            split='test',
        )
        dataset = datasets.concatenate_datasets([dataset_sub1, dataset_sub2])
    elif dataset_name == "math-500":
        try: 
            dataset = dataset_loader.load_dataset(
                dataset_name='HuggingFaceH4/MATH-500',
                split=split,
                dataset_key_map=
                    {
                        "question": "problem",
                    }
            )
        except Exception as e:
            print(f"Error loading dataset from datasets library: {e}")
    elif dataset_name == "minervamath":
        dataset = dataset_loader.load_dataset(
            dataset_name='math-ai/minervamath',
            split=split,
        )
    elif dataset_name == 'aime2024':
        dataset = dataset_loader.load_dataset(
            dataset_name='HuggingFaceH4/aime_2024',
            split="train",
            dataset_key_map={
                "question": "problem",
            }
        )
    elif dataset_name == 'amc23':
        dataset = dataset_loader.load_dataset(
            dataset_name='math-ai/amc23',
            split=split,
        )
    else:
        print(f"Unknown dataset: {dataset_name}")

    return dataset

if __name__ == '__main__':
    dataset = load_format_test_datasets("amc23")
    print(dataset.select(range(10))[7])
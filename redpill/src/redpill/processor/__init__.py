"""Processor module for data flattening and profiling."""

from redpill.processor.processor import DataProcessor
from redpill.processor.flattener import DataFlattener
from redpill.processor.profiler import DataProfiler

__all__ = ["DataProcessor", "DataFlattener", "DataProfiler"]

from collections import defaultdict

from moose.compiler.fixedpoint.host_encoding_pass import HostEncodingPass
from moose.compiler.fixedpoint.host_lowering_pass import HostLoweringPass
from moose.compiler.fixedpoint.host_ring_lowering_pass import HostRingLoweringPass
from moose.compiler.host import NetworkingPass
from moose.compiler.pruning import PruningPass
from moose.compiler.render import render_computation
from moose.compiler.replicated.encoding_pass import ReplicatedEncodingPass
from moose.compiler.replicated.lowering_pass import ReplicatedLoweringPass
from moose.compiler.replicated.replicated_pass import ReplicatedOpsPass
from moose.computation.base import Computation
from moose.deprecated.compiler.mpspdz import MpspdzApplyFunctionPass
from moose.logger import get_logger


class Compiler:
    def __init__(self, passes=None, ring=64):
        self.passes = (
            passes
            if passes is not None
            else [
                MpspdzApplyFunctionPass(),
                HostEncodingPass(),
                HostLoweringPass(),
                ReplicatedEncodingPass(),
                ReplicatedOpsPass(),
                HostRingLoweringPass(),
                ReplicatedLoweringPass(ring=ring),
                PruningPass(),
                NetworkingPass(),
            ]
        )
        self.name_counters = defaultdict(int)

    def run_passes(
        self,
        computation: Computation,
        render=False,
        render_edge_types=True,
        render_prefix="pass",
    ) -> Computation:
        if render:
            render_computation(
                computation,
                filename_prefix=f"{render_prefix}-0-initial",
                render_edge_types=render_edge_types,
            )
        for i, compiler_pass in enumerate(self.passes):
            computation, performed_changes = compiler_pass.run(
                computation, context=self
            )
            if render and performed_changes:
                render_computation(
                    computation,
                    filename_prefix=(
                        f"{render_prefix}-{i+1}"
                        f"-{type(compiler_pass).__name__.lower()}"
                    ),
                    render_edge_types=render_edge_types,
                )
        return computation

    def compile(
        self,
        computation: Computation,
        render=False,
        render_edge_types=True,
        render_prefix="pass",
    ) -> Computation:
        computation = self.run_passes(
            computation, render, render_edge_types, render_prefix,
        )
        for op in computation.operations.values():
            get_logger().debug(f"Computation: {op}")
        return computation

    def get_fresh_name(self, prefix):
        count = self.name_counters[prefix]
        self.name_counters[prefix] += 1
        return f"{prefix}_{count}"

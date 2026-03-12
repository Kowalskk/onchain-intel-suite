import React, { useEffect, useRef, useMemo } from 'react';
import * as d3 from 'd3';
import type { TraceGraph } from '../types';

interface Props {
    graph: TraceGraph;
    onNodeClick: (address: string) => void;
    selectedNodeId: string | null;
}

export const GraphVisualization: React.FC<Props> = ({ graph, onNodeClick, selectedNodeId }) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // We need to clone nodes/edges because D3 mutates them
    const initialData = useMemo(() => ({
        nodes: graph.nodes.map(n => ({ ...n })),
        edges: graph.edges.map(e => ({ ...e }))
    }), [graph]);

    useEffect(() => {
        if (!svgRef.current || !containerRef.current) return;

        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;

        const svg = d3.select(svgRef.current);
        svg.selectAll("*").remove(); // Clear previous

        const g = svg.append("g");

        // Zoom behavior
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => g.attr("transform", event.transform));

        svg.call(zoom);

        // Forces
        const simulation = d3.forceSimulation<any>(initialData.nodes)
            .force("link", d3.forceLink<any, any>(initialData.edges).id(d => d.id).distance(120).strength(1))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(50));

        // Markers for arrows
        svg.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "-0 -5 10 10")
            .attr("refX", 25) // Offset from center
            .attr("refY", 0)
            .attr("orient", "auto")
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .append("svg:path")
            .attr("d", "M 0,-5 L 10 ,0 L 0,5")
            .attr("fill", "var(--sol-border-em)")
            .style("stroke", "none");

        // Links
        const link = g.append("g")
            .selectAll("line")
            .data(initialData.edges)
            .enter().append("line")
            .attr("stroke", d => d.token === 'SOL' ? 'var(--sol-yellow)' : 'var(--sol-cyan)')
            .attr("stroke-opacity", 0.4)
            .attr("stroke-width", d => Math.min(Math.sqrt(d.txCount) + 1, 6))
            .attr("marker-end", "url(#arrowhead)");

        // Nodes
        const node = g.append("g")
            .selectAll(".node")
            .data(initialData.nodes)
            .enter().append("g")
            .attr("class", "node")
            .style("cursor", "pointer")
            .on("click", (_event, d: any) => onNodeClick(d.id))
            .call(d3.drag<any, any>()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended) as any);

        // Node Circles
        node.append("circle")
            .attr("r", d => d.isRoot ? 12 : 8)
            .attr("fill", d => d.isRoot ? 'var(--sol-orange)' : 'var(--sol-bg-secondary)')
            .attr("stroke", d => d.id === selectedNodeId ? 'var(--sol-cyan)' : 'var(--sol-border-em)')
            .attr("stroke-width", d => d.id === selectedNodeId ? 3 : 1.5);

        // Node Labels
        node.append("text")
            .attr("dy", 24)
            .attr("text-anchor", "middle")
            .attr("font-family", "JetBrains Mono, monospace")
            .attr("font-size", "10px")
            .attr("fill", "var(--sol-text-primary)")
            .text(d => d.label);

        // Ticker
        simulation.on("tick", () => {
            link
                .attr("x1", (d: any) => d.source.x)
                .attr("y1", (d: any) => d.source.y)
                .attr("x2", (d: any) => d.target.x)
                .attr("y2", (d: any) => d.target.y);

            node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
        });

        // Dragging functions
        function dragstarted(event: any) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event: any) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event: any) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }

        return () => {
            simulation.stop();
        };
    }, [initialData, onNodeClick, selectedNodeId]);

    return (
        <div ref={containerRef} className="graph-container" style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden', borderRadius: '12px' }}>
            <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />

            {/* Legend / Overlay */}
            <div style={{ position: 'absolute', bottom: '16px', left: '16px', background: 'var(--sol-bg-secondary)', padding: '8px 12px', borderRadius: '6px', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', border: '1px solid var(--sol-border)', opacity: 0.8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ width: '10px', height: '2px', background: 'var(--sol-yellow)' }} /> SOL Flow
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '10px', height: '2px', background: 'var(--sol-cyan)' }} /> Token Flow
                </div>
            </div>
        </div>
    );
};

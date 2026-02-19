import React from 'react';
import { Stage, Layer, Text, Rect, Group, Circle } from 'react-konva';

const KIND_COLORS = {
  Deployment: '#4a9eff',
  Service: '#00ff88',
  Ingress: '#ff6b6b',
  Pod: '#ffd93d',
  ConfigMap: '#a855f7',
  Secret: '#f97316',
};

const KIND_ICONS = {
  Deployment: '📦',
  Service: '🔌',
  Ingress: '🌐',
  Pod: '📄',
  ConfigMap: '⚙️',
  Secret: '🔐',
};

export const GraphCanvas = ({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
  onNodeMove,
  hoveredNodeId,
  onHoverNode,
  particleOffset,
}) => {
  const [stageSize, setStageSize] = React.useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });
  const [containerPos, setContainerPos] = React.useState({ x: 0, y: 0 });
  const [scale, setScale] = React.useState(1);

  React.useEffect(() => {
    const handleResize = () => {
      setStageSize({ width: window.innerWidth, height: window.innerHeight });
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleWheel = (e) => {
    e.evt.preventDefault();
    const stage = e.target.getStage();
    const pointer = stage.getPointerPosition();
    const oldScale = scale;
    const mousePointTo = {
      x: (pointer.x - containerPos.x) / oldScale,
      y: (pointer.y - containerPos.y) / oldScale,
    };
    const direction = e.evt.deltaY > 0 ? -1 : 1;
    const newScale = direction > 0 ? oldScale * 1.1 : oldScale / 1.1;
    const clampedScale = Math.max(0.3, Math.min(3, newScale));
    setScale(clampedScale);
    setContainerPos({
      x: pointer.x - mousePointTo.x * clampedScale,
      y: pointer.y - mousePointTo.y * clampedScale,
    });
  };

  const getNodeColor = (kind) => KIND_COLORS[kind] || '#888888';
  const getNodeIcon = (kind) => KIND_ICONS[kind] || '📄';

  return (
    <Stage
      width={stageSize.width}
      height={stageSize.height}
      x={containerPos.x}
      y={containerPos.y}
      scaleX={scale}
      scaleY={scale}
      onWheel={handleWheel}
      draggable
      onMouseDown={(e) => {
        if (e.target === e.target.getStage()) {
          onSelectNode(null);
        }
      }}
    >
      <Layer>
        {/* Edges with particle animations */}
        {edges.map((edge, i) => {
          const fromNode = nodes.find(n => n.id === edge.from);
          const toNode = nodes.find(n => n.id === edge.to);
          if (!fromNode || !toNode) return null;

          const dx = toNode.visual.x - fromNode.visual.x;
          const dy = toNode.visual.y - fromNode.visual.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          const particles = [];
          const particleCount = Math.floor(distance / 25);

          for (let p = 0; p < particleCount; p++) {
            const basePos = (p / particleCount) * distance;
            for (let s = 0; s < 3; s++) {
              const sizeOffset = s * 15;
              const animatedPos = (basePos + particleOffset * 0.5 + sizeOffset) % distance;
              const particleX = fromNode.visual.x + (animatedPos / distance) * dx;
              const particleY = fromNode.visual.y + (animatedPos / distance) * dy;
              const particleSize = 3 + s * 2;
              const pulsePhase = (particleOffset + p * 10 + s * 20) % 100;
              const opacity = pulsePhase < 50 ? pulsePhase / 50 : (100 - pulsePhase) / 50;

              if (opacity > 0.1) {
                particles.push(
                  <Rect
                    key={`${i}-${p}-${s}`}
                    x={particleX - particleSize / 2}
                    y={particleY - particleSize / 2}
                    width={particleSize}
                    height={particleSize}
                    fill="#ffe6f0"
                    opacity={opacity}
                  />
                );
              }
            }
          }

          return <React.Fragment key={i}>{particles}</React.Fragment>;
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const isSelected = selectedNodeId === node.id;
          const isHovered = hoveredNodeId === node.id;
          const color = getNodeColor(node.kind);
          const icon = getNodeIcon(node.kind);
          const size = node.visual.width || 64;
          const hasError = false;

          return (
            <Group
              key={node.id}
              x={node.visual.x}
              y={node.visual.y}
              scaleX={isHovered || isSelected ? 1.1 : 1}
              scaleY={isHovered || isSelected ? 1.1 : 1}
              draggable
              onDragEnd={(e) => {
                onNodeMove(node.id, e.target.x(), e.target.y());
              }}
              onMouseEnter={() => onHoverNode(node.id)}
              onMouseLeave={() => onHoverNode(null)}
              onClick={() => onSelectNode(node.id)}
            >
              {/* Node background */}
              <Circle
                x={0}
                y={0}
                radius={size / 2}
                fill={color}
                opacity={0.2}
                stroke={color}
                strokeWidth={isSelected ? 3 : 2}
                shadowColor={color}
                shadowBlur={isSelected ? 20 : 10}
              />

              {/* Icon */}
              <Text
                text={icon}
                x={-10}
                y={-12}
                fontSize={20}
                align="center"
              />

              {/* Kind label */}
              <Text
                text={node.kind}
                y={size / 2 + 4}
                fontSize={10}
                fill={color}
                align="center"
                width={size + 20}
                offsetX={(size + 20) / 2}
                fontFamily="monospace"
              />

              {/* Name label */}
              <Text
                text={node.name}
                y={size / 2 + 16}
                fontSize={11}
                fill="#e0e0e0"
                align="center"
                width={size + 40}
                offsetX={(size + 40) / 2}
                fontFamily="monospace"
              />

              {/* Error indicator */}
              {hasError && (
                <Circle
                  x={size / 2 - 5}
                  y={-size / 2 + 5}
                  radius={6}
                  fill="#ff6b6b"
                />
              )}
            </Group>
          );
        })}
      </Layer>
    </Stage>
  );
};

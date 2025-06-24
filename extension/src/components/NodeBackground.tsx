import React, { useEffect, useRef } from 'react';

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  connections: number[];
  opacity: number;
  targetOpacity: number;
  glowIntensity: number;
  nextConnections: number[];
  connectionTransition: number;
  targetX: number;
  targetY: number;
  initialX: number;
  initialY: number;
}

interface Props {
  isScanning: boolean;
}

const NodeBackground: React.FC<Props> = ({ isScanning }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const animationFrameRef = useRef<number>();
  const transitionRef = useRef<number>(0);
  const isTransitioning = useRef<boolean>(false);
  const rotationAngleRef = useRef<number>(0);

  const createRandomConnections = (nodeIndex: number, totalNodes: number) => {
    const connections: number[] = [];
    const numConnections = Math.floor(Math.random() * 2) + 1;
    for (let j = 0; j < numConnections; j++) {
      const target = Math.floor(Math.random() * totalNodes);
      if (target !== nodeIndex && !connections.includes(target)) {
        connections.push(target);
      }
    }
    return connections;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };
    resize();
    window.addEventListener('resize', resize);

    // Initialize nodes
    const initNodes = () => {
      const numNodes = 20;
      const nodes: Node[] = [];
      
      for (let i = 0; i < numNodes; i++) {
        const initialX = Math.random() * canvas.offsetWidth;
        const initialY = Math.random() * canvas.offsetHeight;
        const initialConnections = createRandomConnections(i, numNodes);
        nodes.push({
          x: initialX,
          y: initialY,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          connections: initialConnections,
          nextConnections: initialConnections,
          opacity: 0.6,
          targetOpacity: 0.6,
          glowIntensity: 0,
          connectionTransition: 1,
          targetX: initialX,
          targetY: initialY,
          initialX: initialX,
          initialY: initialY
        });
      }

      nodesRef.current = nodes;
    };

    initNodes();

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);

      // Update transition progress
      if (isTransitioning.current) {
        transitionRef.current = Math.min(1, transitionRef.current + 0.02);
      } else {
        transitionRef.current = Math.max(0, transitionRef.current - 0.02);
      }

      // Update rotation angle during scanning
      if (isScanning && transitionRef.current > 0.5) {
        rotationAngleRef.current += 0.002;
      }

      const centerX = canvas.offsetWidth / 2;
      const centerY = canvas.offsetHeight / 2;
      const radius = Math.min(centerX, centerY) * 0.6;

      // Update node positions and properties
      nodesRef.current = nodesRef.current.map((node, index) => {
        let newX = node.x;
        let newY = node.y;
        let newOpacity = node.opacity;
        let newGlowIntensity = node.glowIntensity;
        let newConnectionTransition = node.connectionTransition;

        // Interpolate opacity and glow
        const opacityDiff = node.targetOpacity - node.opacity;
        newOpacity += opacityDiff * 0.1;
        
        const targetGlow = isScanning ? 1 : 0;
        const glowDiff = targetGlow - node.glowIntensity;
        newGlowIntensity += glowDiff * 0.05;

        // Update connection transition
        if (isScanning) {
          newConnectionTransition = Math.max(0, node.connectionTransition - 0.05);
        } else {
          newConnectionTransition = Math.min(1, node.connectionTransition + 0.05);
        }

        // Calculate target position based on scanning state
        if (isScanning) {
          const angle = ((index / nodesRef.current.length) * Math.PI * 2) + rotationAngleRef.current;
          node.targetX = centerX + Math.cos(angle) * radius;
          node.targetY = centerY + Math.sin(angle) * radius;
        }

        // Smooth position transition with slower factor when not scanning
        const transitionFactor = isScanning ? 0.1 : 0.03;
        const targetXDiff = node.targetX - node.x;
        const targetYDiff = node.targetY - node.y;
        newX += targetXDiff * transitionFactor;
        newY += targetYDiff * transitionFactor;

        // Only apply random movement when fully transitioned out of scanning
        const distanceToTarget = Math.sqrt(
          Math.pow(targetXDiff, 2) + Math.pow(targetYDiff, 2)
        );

        if (!isScanning && distanceToTarget < 1) {
          newX += node.vx;
          newY += node.vy;

          // Bounce off walls
          if (newX < 0 || newX > canvas.offsetWidth) {
            node.vx *= -1;
            newX = Math.max(0, Math.min(newX, canvas.offsetWidth));
          }
          if (newY < 0 || newY > canvas.offsetHeight) {
            node.vy *= -1;
            newY = Math.max(0, Math.min(newY, canvas.offsetHeight));
          }

          // Update target to follow current position
          node.targetX = newX;
          node.targetY = newY;
        }

        return {
          ...node,
          x: newX,
          y: newY,
          opacity: newOpacity,
          glowIntensity: newGlowIntensity,
          connectionTransition: newConnectionTransition
        };
      });

      // Draw connections
      nodesRef.current.forEach(node => {
        // Draw current connections with fade out
        node.connections.forEach(targetIndex => {
          const target = nodesRef.current[targetIndex];
          drawConnection(ctx, node, target, node.connectionTransition);
        });

        // Draw next connections with fade in
        node.nextConnections.forEach(targetIndex => {
          const target = nodesRef.current[targetIndex];
          drawConnection(ctx, node, target, 1 - node.connectionTransition);
        });
      });

      // Draw nodes
      nodesRef.current.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 2 + (node.glowIntensity * 1), 0, Math.PI * 2);
        
        // Interpolate node color
        const blue = Math.floor(node.glowIntensity * 165);
        const gray = Math.floor(113 + (node.glowIntensity * (165 - 113)));
        ctx.fillStyle = isScanning ? 
          `rgb(96, ${blue}, 250)` : 
          `rgb(113, ${gray}, 150)`;
        
        ctx.globalAlpha = node.opacity;
        
        // Interpolate shadow blur
        if (node.glowIntensity > 0) {
          ctx.shadowColor = '#60A5FA';
          ctx.shadowBlur = 15 * node.glowIntensity;
        } else {
          ctx.shadowBlur = 0;
        }
        ctx.fill();
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    const drawConnection = (
      ctx: CanvasRenderingContext2D,
      node: Node,
      target: Node,
      opacity: number
    ) => {
      if (opacity <= 0) return;
      
      ctx.beginPath();
      ctx.moveTo(node.x, node.y);
      ctx.lineTo(target.x, target.y);
      
      // Interpolate connection color
      const blue = Math.floor(node.glowIntensity * 165);
      const gray = Math.floor(74 + (node.glowIntensity * (165 - 74)));
      ctx.strokeStyle = isScanning ? 
        `rgb(96, ${blue}, 250)` : 
        `rgb(74, ${gray}, 104)`;
      
      ctx.lineWidth = 1 + (node.glowIntensity * 0.5);
      ctx.globalAlpha = node.opacity * 0.3 * opacity;
      
      // Interpolate shadow blur
      if (node.glowIntensity > 0) {
        ctx.shadowColor = '#60A5FA';
        ctx.shadowBlur = 10 * node.glowIntensity;
      } else {
        ctx.shadowBlur = 0;
      }
      ctx.stroke();
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      window.removeEventListener('resize', resize);
    };
  }, [isScanning]);

  useEffect(() => {
    if (isScanning) {
      isTransitioning.current = true;
      rotationAngleRef.current = 0;

      nodesRef.current.forEach((node, i) => {
        node.connections = [...node.nextConnections];
        node.nextConnections = [(i + 1) % nodesRef.current.length];
        node.targetOpacity = 0.8;
        node.connectionTransition = 1;
      });
    } else {
      // Keep transitioning true until nodes reach their targets
      isTransitioning.current = true;

      nodesRef.current.forEach((node, i) => {
        node.connections = [...node.nextConnections];
        node.nextConnections = createRandomConnections(i, nodesRef.current.length);
        node.targetOpacity = 0.6;
        node.connectionTransition = 0;
        
        // Set target position with smaller radius and relative to current position
        const randomAngle = Math.random() * Math.PI * 2;
        const randomRadius = Math.random() * 30 + 20; // Smaller radius between 20 and 50
        node.targetX = node.x + Math.cos(randomAngle) * randomRadius;
        node.targetY = node.y + Math.sin(randomAngle) * randomRadius;
        
        // Slower random movement
        node.vx = (Math.random() - 0.5) * 0.2;
        node.vy = (Math.random() - 0.5) * 0.2;
      });
    }
  }, [isScanning]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
      style={{ background: 'transparent', zIndex: 0 }}
    />
  );
};

export default NodeBackground; 
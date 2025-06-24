import React, { useEffect, useRef } from 'react';

interface AnimatedBackgroundProps {
  isScanning: boolean;
}

const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({ isScanning }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const glowIntensityRef = useRef(0);
  const scanProgressRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match container size
    const resizeCanvas = () => {
      if (!canvas) return;
      const container = canvas.parentElement;
      if (!container) return;
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Node class to manage each point in the network
    class Node {
      x: number = 0;
      y: number = 0;
      vx: number = 0;
      vy: number = 0;
      radius: number = 1;
      targetX: number = 0;
      targetY: number = 0;

      constructor() {
        if (!canvas) return;
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 0.3;
        this.vy = (Math.random() - 0.5) * 0.3;
        this.targetX = this.x;
        this.targetY = this.y;
      }

      update(isScanning: boolean, scanProgress: number) {
        if (!canvas) return;

        if (isScanning) {
          // During scanning, nodes move more deliberately
          const dx = this.targetX - this.x;
          const dy = this.targetY - this.y;
          this.x += dx * 0.05;
          this.y += dy * 0.05;

          // Update target positions to create a wave effect
          if (this.y < scanProgress) {
            this.targetY = this.y + Math.sin(this.x / 30) * 20;
          }
        } else {
          // Normal movement
          this.x += this.vx;
          this.y += this.vy;

          // Bounce off edges
          if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
          if (this.y < 0 || this.y > canvas.height) this.vy *= -1;

          // Reset target positions
          this.targetX = this.x;
          this.targetY = this.y;
        }
      }

      draw() {
        if (!ctx) return;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.fill();
      }
    }

    // Create nodes - fewer nodes for better performance in popup
    const nodes: Node[] = Array.from({ length: 30 }, () => new Node());

    // Animation loop
    const animate = () => {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Update glow intensity for pulsing effect during scanning
      if (isScanning) {
        glowIntensityRef.current = 0.3 + Math.sin(Date.now() / 500) * 0.2;
        scanProgressRef.current += 2;
        if (scanProgressRef.current > canvas.height) {
          scanProgressRef.current = 0;
        }
      } else {
        glowIntensityRef.current = 0.08;
        scanProgressRef.current = 0;
      }

      // Update and draw nodes
      nodes.forEach(node => {
        node.update(isScanning, scanProgressRef.current);
        node.draw();
      });

      // Draw connections
      nodes.forEach((node, i) => {
        nodes.slice(i + 1).forEach(otherNode => {
          const dx = node.x - otherNode.x;
          const dy = node.y - otherNode.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const maxDistance = isScanning ? 120 : 80; // Increased connection distance during scanning

          if (distance < maxDistance) {
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(otherNode.x, otherNode.y);
            
            // Calculate connection opacity based on distance and scanning state
            const baseOpacity = isScanning ? glowIntensityRef.current : 0.08;
            const opacity = baseOpacity * (1 - distance / maxDistance);
            
            // Create glowing effect for connections
            const gradient = ctx.createLinearGradient(node.x, node.y, otherNode.x, otherNode.y);
            gradient.addColorStop(0, `rgba(255, 255, 255, ${opacity})`);
            gradient.addColorStop(0.5, `rgba(255, 255, 255, ${opacity * 1.5})`);
            gradient.addColorStop(1, `rgba(255, 255, 255, ${opacity})`);
            
            ctx.strokeStyle = gradient;
            ctx.lineWidth = isScanning ? 1 : 0.5;
            ctx.stroke();
          }
        });
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      window.removeEventListener('resize', resizeCanvas);
    };
  }, [isScanning]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
      style={{ background: 'rgb(0, 0, 0)' }}
    />
  );
};

export default AnimatedBackground; 
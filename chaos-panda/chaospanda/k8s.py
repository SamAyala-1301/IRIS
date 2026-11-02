"""
chaospanda/k8s.py — Kubernetes helpers
"""
from kubernetes import client, config


def load_cluster():
    config.load_kube_config()
    return client.CoreV1Api()


def count_ready(v1, namespace, deployment):
    """
    Returns count of pods that are:
      - labeled for this deployment
      - not terminating (deletion_timestamp is None)
      - phase == Running
      - all containers reporting ready
    """
    pods = v1.list_namespaced_pod(
        namespace,
        label_selector=f"app={deployment}"
    )
    ready = 0
    for p in pods.items:
        if p.metadata.deletion_timestamp is not None:
            continue
        if p.status.phase != "Running":
            continue
        containers = p.status.container_statuses or []
        if containers and all(cs.ready for cs in containers):
            ready += 1
    return ready


def get_running_pods(v1, namespace, deployment):
    pods = v1.list_namespaced_pod(
        namespace,
        label_selector=f"app={deployment}"
    )
    return [
        p for p in pods.items
        if p.metadata.deletion_timestamp is None
        and p.status.phase == "Running"
    ]


def kill_pod(v1, pod):
    v1.delete_namespaced_pod(pod.metadata.name, pod.metadata.namespace)
    print(f"[CHAOS]  Killed: {pod.metadata.name}")
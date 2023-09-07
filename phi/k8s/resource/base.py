from typing import Any, Dict, List, Optional

from pydantic import Field, BaseModel, ConfigDict, field_serializer

from phi.resource.base import ResourceBase
from phi.k8s.api_client import K8sApiClient
from phi.k8s.constants import DEFAULT_K8S_NAMESPACE
from phi.k8s.enums.api_version import ApiVersion
from phi.k8s.enums.kind import Kind
from phi.k8s.resource.meta.v1.object_meta import ObjectMeta
from phi.cli.console import print_info
from phi.utils.log import logger


class K8sObject(BaseModel):
    def get_k8s_object(self) -> Any:
        """Creates a K8sObject for this resource.
        Eg:
            * For a Deployment resource, it will return the V1Deployment object.
        """
        logger.error("@get_k8s_object method not defined")

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)


class K8sResource(ResourceBase, K8sObject):
    """Base class for K8s Resources"""

    # Common fields for all K8s Resources
    # Which version of the Kubernetes API you're using to create this object
    # Note: we use an alias "apiVersion" so that the K8s manifest generated by this resource
    #       has the correct key
    api_version: ApiVersion = Field(..., alias="apiVersion")
    # What kind of object you want to create
    kind: Kind
    # Data that helps uniquely identify the object, including a name string, UID, and optional namespace
    metadata: ObjectMeta

    # Fields used in api calls
    # async_req bool: execute request asynchronously
    async_req: bool = False
    # pretty: If 'true', then the output is pretty printed.
    pretty: bool = True

    # List of fields to include from the K8sResource base class when generating the
    # K8s manifest. Subclasses should add fields to the fields_for_k8s_manifest list to include them in the manifest.
    fields_for_k8s_manifest_base: List[str] = [
        "api_version",
        "apiVersion",
        "kind",
        "metadata",
    ]
    # List of fields to include from Subclasses when generating the K8s manifest.
    # This should be defined by the Subclass
    fields_for_k8s_manifest: List[str] = []

    k8s_client: Optional[K8sApiClient] = None

    @field_serializer("api_version")
    def get_api_version_value(self, v) -> str:
        return v.value

    @field_serializer("kind")
    def get_kind_value(self, v) -> str:
        return v.value

    def get_resource_name(self) -> str:
        return self.name or self.metadata.name or self.__class__.__name__

    def get_namespace(self) -> str:
        if self.metadata and self.metadata.namespace:
            return self.metadata.namespace
        return DEFAULT_K8S_NAMESPACE

    def get_label_selector(self) -> str:
        labels = self.metadata.labels
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
            return label_str
        return ""

    @staticmethod
    def get_from_cluster(k8s_client: K8sApiClient, namespace: Optional[str] = None, **kwargs) -> Any:
        """Gets all resources of this type from the k8s cluster"""
        logger.error("@get_from_cluster method not defined")
        return None

    def get_k8s_client(self) -> K8sApiClient:
        if self.k8s_client is not None:
            return self.k8s_client
        self.k8s_client = K8sApiClient()
        return self.k8s_client

    def _read(self, k8s_client: K8sApiClient) -> Any:
        logger.error(f"@_read method not defined for {self.get_resource_name()}")
        return True

    def read(self, k8s_client: K8sApiClient) -> Any:
        """Reads the resource from the k8s cluster
        Eg:
            * For a Deployment resource, it will return the V1Deployment object
            currently running on the cluster.
        """
        # Step 1: Use cached value if available
        if self.use_cache and self.active_resource is not None:
            return self.active_resource

        # Step 2: Skip resource creation if skip_read = True
        if self.skip_read:
            print_info(f"Skipping read: {self.get_resource_name()}")
            return True

        # Step 3: Read resource
        client: K8sApiClient = k8s_client or self.get_k8s_client()
        return self._read(client)

    def is_active(self, k8s_client: K8sApiClient) -> bool:
        """Returns True if the resource is active on the k8s cluster"""
        self.active_resource = self._read(k8s_client=k8s_client)
        return True if self.active_resource is not None else False

    def _create(self, k8s_client: K8sApiClient) -> bool:
        logger.error(f"@_create method not defined for {self.get_resource_name()}")
        return True

    def create(self, k8s_client: K8sApiClient) -> bool:
        """Creates the resource on the k8s Cluster"""

        # Step 1: Skip resource creation if skip_create = True
        if self.skip_create:
            print_info(f"Skipping create: {self.get_resource_name()}")
            return True

        # Step 2: Check if resource is active and use_cache = True
        client: K8sApiClient = k8s_client or self.get_k8s_client()
        if self.use_cache and self.is_active(client):
            self.resource_created = True
            print_info(f"{self.get_resource_type()}: {self.get_resource_name()} already exists")
            return True
        # Step 3: Create the resource
        else:
            self.resource_created = self._create(client)
            if self.resource_created:
                print_info(f"{self.get_resource_type()}: {self.get_resource_name()} created")

        # Step 4: Run post create steps
        if self.resource_created:
            if self.save_output:
                self.save_output_file()
            logger.debug(f"Running post-create for {self.get_resource_type()}: {self.get_resource_name()}")
            return self.post_create(client)
        logger.error(f"Failed to create {self.get_resource_type()}: {self.get_resource_name()}")
        return self.resource_created

    def post_create(self, k8s_client: K8sApiClient) -> bool:
        return True

    def _update(self, k8s_client: K8sApiClient) -> Any:
        logger.error(f"@_update method not defined for {self.get_resource_name()}")
        return True

    def update(self, k8s_client: K8sApiClient) -> bool:
        """Updates the resource on the k8s Cluster"""

        # Step 1: Skip resource update if skip_update = True
        if self.skip_update:
            print_info(f"Skipping update: {self.get_resource_name()}")
            return True

        # Step 2: Update the resource
        client: K8sApiClient = k8s_client or self.get_k8s_client()
        if self.is_active(client):
            self.resource_updated = self._update(client)
        else:
            print_info(f"{self.get_resource_type()}: {self.get_resource_name()} does not exist")
            return True

        # Step 3: Run post update steps
        if self.resource_updated:
            print_info(f"{self.get_resource_type()}: {self.get_resource_name()} updated")
            if self.save_output:
                self.save_output_file()
            logger.debug(f"Running post-update for {self.get_resource_type()}: {self.get_resource_name()}")
            return self.post_update(client)
        logger.error(f"Failed to update {self.get_resource_type()}: {self.get_resource_name()}")
        return self.resource_updated

    def post_update(self, k8s_client: K8sApiClient) -> bool:
        return True

    def _delete(self, k8s_client: K8sApiClient) -> Any:
        logger.error(f"@_delete method not defined for {self.get_resource_name()}")
        return True

    def delete(self, k8s_client: K8sApiClient) -> bool:
        """Deletes the resource from the k8s cluster"""

        # Step 1: Skip resource deletion if skip_delete = True
        if self.skip_delete:
            print_info(f"Skipping delete: {self.get_resource_name()}")
            return True

        # Step 2: Delete the resource
        client: K8sApiClient = k8s_client or self.get_k8s_client()
        if self.is_active(client):
            self.resource_deleted = self._delete(client)
        else:
            print_info(f"{self.get_resource_type()}: {self.get_resource_name()} does not exist")
            return True

        # Step 3: Run post delete steps
        if self.resource_deleted:
            print_info(f"{self.get_resource_type()}: {self.get_resource_name()} deleted")
            if self.save_output:
                self.delete_output_file()
            logger.debug(f"Running post-delete for {self.get_resource_type()}: {self.get_resource_name()}.")
            return self.post_delete(client)
        logger.error(f"Failed to delete {self.get_resource_type()}: {self.get_resource_name()}")
        return self.resource_deleted

    def post_delete(self, k8s_client: K8sApiClient) -> bool:
        return True

    ######################################################
    ## Function to get the k8s manifest
    ######################################################

    def get_k8s_manifest_dict(self) -> Optional[Dict[str, Any]]:
        """Returns the K8s Manifest for this Object as a dict"""

        from itertools import chain

        k8s_manifest: Dict[str, Any] = {}
        all_attributes: Dict[str, Any] = self.model_dump(exclude_defaults=True, by_alias=True)
        # logger.debug("All Attributes: {}".format(all_attributes))
        for attr_name in chain(self.fields_for_k8s_manifest_base, self.fields_for_k8s_manifest):
            if attr_name in all_attributes:
                k8s_manifest[attr_name] = all_attributes[attr_name]
        logger.debug(f"k8s_manifest:\n{k8s_manifest}")
        return k8s_manifest

    def get_k8s_manifest_yaml(self, **kwargs) -> Optional[str]:
        """Returns the K8s Manifest for this Object as a yaml"""

        import yaml

        k8s_manifest_dict = self.get_k8s_manifest_dict()

        if k8s_manifest_dict is not None:
            return yaml.safe_dump(k8s_manifest_dict, **kwargs)
        return None

    def get_k8s_manifest_json(self, **kwargs) -> Optional[str]:
        """Returns the K8s Manifest for this Object as a json"""

        import json

        k8s_manifest_dict = self.get_k8s_manifest_dict()

        if k8s_manifest_dict is not None:
            return json.dumps(k8s_manifest_dict, **kwargs)
        return None

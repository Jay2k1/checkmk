<script setup lang="ts">
import { computed, ref } from 'vue'
import { validate_value, type ValidationMessages } from '@/utils'
import { FormValidation } from '@/components/cmk-form/'
import * as FormSpec from '@/vue_formspec_components'

const props = defineProps<{
  spec: FormSpec.String
}>()

const validation = ref<ValidationMessages>([])
function setValidation(new_validation: ValidationMessages) {
  new_validation.forEach((message) => {
    data.value = message.invalid_value as string
  })
  validation.value = new_validation
}

defineExpose({
  setValidation
})

const data = defineModel('data', { type: String, required: true })
const local_validation = ref<ValidationMessages | null>(null)

const emit = defineEmits<{
  (e: 'update:data', value: number | string): void
}>()

const value = computed({
  get(): string {
    return data.value
  },
  set(value: string) {
    local_validation.value = []
    validate_value(value, props.spec.validators!).forEach((error) => {
      local_validation.value = [{ message: error, location: [], invalid_value: value }]
    })
    emit('update:data', value)
  }
})
</script>

<template>
  <label :for="$componentId">{{ props.spec.title }}</label>
  <input :id="$componentId" v-model="value" type="text" />
  <FormValidation :validation="validation"></FormValidation>
</template>
